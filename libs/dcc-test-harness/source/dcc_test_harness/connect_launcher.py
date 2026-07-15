"""Launch a DCC using ftrack-connect configuration.

Reads YAML launch configs from a built ftrack connect plugin
directory, discovers the DCC executable, builds the connect
environment, and injects the test server.  No ``ftrack_api``
session is required.

Supports two directory layouts:

**Built plugin** (preferred)::

    ftrack-framework-maya-X.Y.Z/
        launch/maya-launch.yaml
        dependencies/
        resource/bootstrap/userSetup.py
        extensions/common/
        extensions/maya/
        hook/

**Source project** (development)::

    projects/framework-maya/
        extensions/launch/maya-launch.yaml
        connect-plugin/dependencies/
        resource/bootstrap/userSetup.py
        extensions/common/
        extensions/maya/

Usage via CLI::

    pytest --dcc-app maya \\
           --dcc-connect-plugin path/to/ftrack-framework-maya
"""

from __future__ import annotations

import logging
import os
import platform
import ssl
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dcc_test_harness._app_discovery import (
    discover_executable,
    load_launch_config,
)
from dcc_test_harness._dcc_profiles import (
    DCCProfile,
    get_profile,
)
from dcc_test_harness.launcher import (
    DCCProcess,
    LaunchConfig,
    Launcher,
)

logger = logging.getLogger(__name__)


def resolve_ftrack_credentials(
    env: Optional[dict] = None,
) -> Optional[dict]:
    """Resolve ftrack server credentials.

    Checks *env* (defaults to ``os.environ``) for ``FTRACK_SERVER``
    and ``FTRACK_API_KEY``/``FTRACK_APIKEY`` (plus optional
    ``FTRACK_API_USER``), falling back to the credentials stored by
    ftrack Connect on login.

    Returns a dict with ``server``, ``api_key`` and ``api_user``
    keys, or ``None`` when no complete credentials are found.
    """
    if env is None:
        env = os.environ

    server = env.get("FTRACK_SERVER")
    api_key = env.get("FTRACK_API_KEY") or env.get("FTRACK_APIKEY")
    api_user = env.get("FTRACK_API_USER")

    if not server or not api_key:
        # Fall back to credentials stored by ftrack Connect.
        # Imported lazily so the harness can be used without
        # ftrack-connect installed (e.g. launch-only tests).
        try:
            from ftrack_connect.utils.credentials import (
                load_credentials,
            )
        except ImportError:
            load_credentials = None

        creds = load_credentials() if load_credentials else None
        if creds:
            for account in creds.get("accounts", []):
                s = account.get("server_url")
                k = account.get("api_key")
                if not (s and k):
                    continue
                # If a server is already known (e.g. from the env), only
                # accept an account that matches it so we never pair the
                # target server with an unrelated API key.
                if server and s != server:
                    continue
                server = server or s
                api_key = api_key or k
                api_user = api_user or account.get("api_user")
                break

    if not server or not api_key:
        return None

    return {
        "server": server,
        "api_key": api_key,
        "api_user": api_user,
    }


def resolve_app_bundle(
    path: str,
    app_bundle_binary: Optional[str] = None,
) -> str:
    """Resolve a macOS .app bundle to its executable.

    On non-macOS platforms, or if *path* doesn't end in ``.app``,
    returns *path* unchanged.

    Args:
        path: Path to the executable or .app bundle.
        app_bundle_binary: Optional relative path from the bundle
            to the binary (e.g. ``"Contents/bin/maya"``).  Falls
            back to the ``CFBundleExecutable`` from Info.plist.
    """
    if platform.system() != "Darwin":
        return path
    if not path.endswith(".app"):
        return path

    if app_bundle_binary:
        resolved = os.path.join(path, app_bundle_binary)
        if os.path.isfile(resolved):
            return resolved

    plist_path = os.path.join(path, "Contents", "Info.plist")
    if os.path.isfile(plist_path):
        import plistlib

        with open(plist_path, "rb") as f:
            info = plistlib.load(f)
        exe_name = info.get("CFBundleExecutable")
        if exe_name:
            resolved = os.path.join(path, "Contents", "MacOS", exe_name)
            if os.path.isfile(resolved):
                return resolved

    raise FileNotFoundError(
        f"Cannot resolve .app bundle to executable: {path}"
    )


@dataclass
class _PluginLayout:
    """Resolved paths for a connect plugin directory."""

    launch_dir: Path
    dependencies_dir: Path
    bootstrap_dir: Path


def _detect_layout(plugin_path: Path) -> _PluginLayout:
    """Auto-detect whether *plugin_path* is a built plugin
    or a source project directory.

    Built plugins have ``launch/`` at the root.
    Source projects have ``extensions/launch/``.
    """
    # Built layout: launch/ at root.
    built_launch = plugin_path / "launch"
    if built_launch.is_dir():
        return _PluginLayout(
            launch_dir=built_launch,
            dependencies_dir=plugin_path / "dependencies",
            bootstrap_dir=(plugin_path / "resource" / "bootstrap"),
        )

    # Source layout: extensions/launch/ + connect-plugin/.
    source_launch = plugin_path / "extensions" / "launch"
    if source_launch.is_dir():
        return _PluginLayout(
            launch_dir=source_launch,
            dependencies_dir=(plugin_path / "connect-plugin" / "dependencies"),
            bootstrap_dir=(plugin_path / "resource" / "bootstrap"),
        )

    raise FileNotFoundError(
        f"Cannot detect plugin layout in {plugin_path}. "
        f"Expected launch/ (built plugin) or "
        f"extensions/launch/ (source project)."
    )


class ConnectLauncher(Launcher):
    """Launch a DCC using ftrack-connect plugin configuration.

    Reads the YAML launch config from a built connect plugin
    (or source project) to discover the executable, then
    builds the environment that replicates what ftrack-connect
    would set up (PYTHONPATH, bootstrap paths, extensions).

    The DCC type is auto-detected from the YAML ``icon`` field
    (e.g. ``"maya"``), or can be overridden via *dcc_app*.

    Args:
        connect_plugin_path: Path to a built connect plugin
            directory or source project directory.
        extra_plugins: Additional plugin paths whose
            environments are layered on top of the primary.
            Each path is a built plugin or source project
            directory.
        dcc_app: Optional DCC name override. If ``None``,
            detected from the launch config YAML.
        dcc_version: Optional version prefix to select
            (e.g. ``"2025"``).  If ``None``, the newest
            discovered version is used.
        launch_config_name: Optional file name of the launch
            config yaml to load (e.g.
            ``"harmony-launch-premium.yaml"``).  If ``None``,
            the launch directory is globbed for
            ``*-launch*.yaml`` files.
    """

    def __init__(
        self,
        connect_plugin_path: str,
        extra_plugins: Optional[list[str]] = None,
        dcc_app: Optional[str] = None,
        dcc_version: Optional[str] = None,
        launch_config_name: Optional[str] = None,
    ) -> None:
        self._dcc_version = dcc_version
        self._launch_config_name = launch_config_name
        self._plugin_path = Path(connect_plugin_path)
        if not self._plugin_path.is_dir():
            raise FileNotFoundError(
                f"Connect plugin path does not exist: {connect_plugin_path}"
            )
        self._layout = _detect_layout(self._plugin_path)
        self._launch_config = self._load_launch_config()
        self._extra_plugins = [Path(p) for p in (extra_plugins or [])]

        # Auto-detect DCC from YAML icon field.
        if dcc_app is None:
            dcc_app = self._launch_config.get("icon")
            if not dcc_app:
                raise ValueError(
                    "Cannot detect DCC type from launch "
                    "config (no 'icon' field). "
                    "Pass --dcc-app explicitly."
                )
            logger.info(
                "Auto-detected DCC: %s (from launch config)",
                dcc_app,
            )

        self._profile: DCCProfile = get_profile(dcc_app)
        self._discovered_version: Optional[str] = None

    def launch(self, config: LaunchConfig) -> DCCProcess:
        """Start the DCC with the test server running."""
        # 1. Find executable.
        if config.dcc_executable:
            executable = config.dcc_executable
        else:
            app = discover_executable(
                self._launch_config,
                version=self._dcc_version,
            )
            executable = app.path
            self._discovered_version = app.version

        # 2. Resolve macOS .app bundle to actual binary.
        executable = self._resolve_app_bundle(executable)

        # 3. Build environment (harness + connect).
        env = self._build_env(config)
        env = self._apply_connect_env(env)

        # 4. Build startup code and command.
        fd, port_file = tempfile.mkstemp(suffix=".port", prefix="dcc_test_")
        os.close(fd)
        startup_code = self._build_server_startup_code(
            port_file,
            config.server_port,
            quit_fn=self._profile.quit_fn,
        )
        cmd = self._build_command(executable, startup_code)

        logger.info(
            "Launching %s via ConnectLauncher: %s",
            self._profile.name,
            cmd[0],
        )

        # 5. Launch.
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # 6. Wait for the test server to be ready.
        try:
            port = self._wait_for_port_file(
                port_file, config.startup_timeout, process
            )
        except Exception:
            process.kill()
            raise
        finally:
            try:
                os.unlink(port_file)
            except OSError:
                pass

        return DCCProcess(process=process, port=port, host="127.0.0.1")

    # -- Connect environment --

    def _apply_connect_env(self, env: dict[str, str]) -> dict[str, str]:
        """Layer ftrack-connect environment on top of *env*.

        Replicates the env vars that the integration's
        ``on_launch_integration`` hook would set, plus the
        server credentials that Connect normally injects.

        Requires ``FTRACK_SERVER`` and ``FTRACK_API_KEY``
        (or ``FTRACK_APIKEY``) in the current environment.
        """
        layout = self._layout

        # -- ftrack server credentials --
        # Connect normally injects these from its session.
        # Check env vars first, fall back to stored credentials.
        credentials = resolve_ftrack_credentials(env)

        if credentials is None:
            raise RuntimeError(
                "Cannot find ftrack server credentials.\n"
                "Either:\n"
                "  - Set FTRACK_SERVER and FTRACK_API_KEY "
                "environment variables\n"
                "  - Or log in via ftrack Connect (stores "
                "credentials automatically)"
            )

        server = credentials["server"]
        api_key = credentials["api_key"]
        api_user = credentials["api_user"]

        env["FTRACK_SERVER"] = server
        env["FTRACK_API_KEY"] = api_key
        env["FTRACK_APIKEY"] = api_key
        if api_user:
            env.setdefault("FTRACK_API_USER", api_user)

        # FTRACK_EVENT_SERVER — Connect sets this so the
        # integration can connect to the event hub.
        env.setdefault("FTRACK_EVENT_SERVER", server)

        # SSL_CERT_FILE — DCC apps often bundle outdated CA
        # certs.  Connect sets this to the system default so
        # the WebSocket event hub can verify the server cert.
        if platform.system() != "Windows":
            cafile = ssl.get_default_verify_paths().cafile
            if cafile:
                env["SSL_CERT_FILE"] = cafile

        # -- Plugin paths and dependencies --

        # PYTHONPATH: prepend dependencies + bootstrap.
        prepend: list[str] = []
        if layout.dependencies_dir.is_dir():
            prepend.append(str(layout.dependencies_dir))
        else:
            logger.warning(
                "No dependencies directory at %s — "
                "ftrack integration packages will not be "
                "available. Build the plugin first.",
                layout.dependencies_dir,
            )
        if layout.bootstrap_dir.is_dir():
            prepend.append(str(layout.bootstrap_dir))

        if prepend:
            existing = env.get("PYTHONPATH", "")
            joined = os.pathsep.join(prepend)
            env["PYTHONPATH"] = (
                joined + os.pathsep + existing if existing else joined
            )

        # DCC-specific script path (e.g. MAYA_SCRIPT_PATH).
        if layout.bootstrap_dir.is_dir():
            env[self._profile.script_path_env] = str(layout.bootstrap_dir)

        # DCC version (e.g. FTRACK_MAYA_VERSION).
        if self._discovered_version:
            env[self._profile.version_env] = self._discovered_version

        # FTRACK_FRAMEWORK_EXTENSIONS_PATH from YAML.
        ext_paths_config = self._launch_config.get("extensions_path", [])
        ext_paths: list[str] = []
        for rel_path in ext_paths_config:
            full = self._plugin_path / rel_path
            if full.is_dir():
                ext_paths.append(str(full))
        if ext_paths:
            env["FTRACK_FRAMEWORK_EXTENSIONS_PATH"] = os.pathsep.join(
                ext_paths
            )

        # Layer extra plugins on top.
        for extra_path in self._extra_plugins:
            self._apply_extra_plugin_env(env, extra_path)

        return env

    def _apply_extra_plugin_env(
        self,
        env: dict[str, str],
        plugin_path: Path,
    ) -> None:
        """Layer an extra plugin's environment on top.

        Probes well-known directories (``dependencies/``,
        ``source/``, ``resource/bootstrap/``,
        ``connect-plugin/dependencies/``) without requiring
        a launch config.  Works for both built plugins and
        source project directories.
        """
        # -- Resolve paths (check both built and source layouts) --
        candidates_deps = [
            plugin_path / "dependencies",
            plugin_path / "connect-plugin" / "dependencies",
        ]
        candidates_bootstrap = [
            plugin_path / "resource" / "bootstrap",
        ]
        source_dir = plugin_path / "source"

        # -- PYTHONPATH --
        prepend: list[str] = []
        for d in candidates_deps:
            if d.is_dir():
                prepend.append(str(d))
                break

        if source_dir.is_dir():
            prepend.append(str(source_dir))

        for d in candidates_bootstrap:
            if d.is_dir():
                prepend.append(str(d))
                break

        if prepend:
            existing = env.get("PYTHONPATH", "")
            joined = os.pathsep.join(prepend)
            env["PYTHONPATH"] = (
                joined + os.pathsep + existing if existing else joined
            )

        # -- DCC script path (e.g. MAYA_SCRIPT_PATH) --
        for d in candidates_bootstrap:
            if d.is_dir():
                key = self._profile.script_path_env
                existing = env.get(key, "")
                bootstrap = str(d)
                env[key] = (
                    existing + os.pathsep + bootstrap
                    if existing
                    else bootstrap
                )
                break

        logger.info("Layered extra plugin: %s", plugin_path)

    # -- Command construction --

    def _build_command(self, executable: str, startup_code: str) -> list[str]:
        """Build the subprocess command list."""
        template = self._profile.command_template
        arg = template.format(code=startup_code)
        return [executable, self._profile.command_flag, arg]

    # -- macOS .app bundle resolution --

    def _resolve_app_bundle(self, path: str) -> str:
        """Resolve a macOS .app bundle to its executable.

        On non-macOS platforms, or if *path* doesn't end in
        ``.app``, returns *path* unchanged.
        """
        return resolve_app_bundle(path, self._profile.app_bundle_binary)

    # -- Launch config loading --

    def _load_launch_config(self) -> dict:
        """Find and load the YAML launch config."""
        launch_dir = self._layout.launch_dir

        if self._launch_config_name:
            explicit = launch_dir / self._launch_config_name
            if not explicit.is_file():
                raise FileNotFoundError(
                    f"Launch config "
                    f"{self._launch_config_name!r} not found "
                    f"in {launch_dir}"
                )
            return load_launch_config(explicit)

        yamls = sorted(launch_dir.glob("*-launch*.yaml"))
        if not yamls:
            raise FileNotFoundError(f"No *-launch.yaml files in {launch_dir}")

        if len(yamls) > 1:
            names = [y.name for y in yamls]
            logger.info(
                "Multiple launch configs found: %s. Using %s",
                names,
                yamls[0].name,
            )

        return load_launch_config(yamls[0])
