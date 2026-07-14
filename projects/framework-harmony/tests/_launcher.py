# :coding: utf-8
# :copyright: Copyright (c) 2026 ftrack

"""Harmony launcher for the DCC test harness.

Launches Harmony the way ftrack Connect does, 1:1:

- the executable is discovered from the same launch config yaml
  Connect uses (``harmony-launch-<variant>.yaml``);
- the ftrack JS package is deployed to the user's Harmony scripts
  folder by calling the connect-plugin hook's own ``sync_js_plugin``;
- the environment Connect would build is replicated
  (``FTRACK_INTEGRATION_LISTEN_PORT``,
  ``FTRACK_REMOTE_INTEGRATION_SESSION_ID``, ``FTRACK_HARMONY_VERSION``,
  PYTHONPATH, ``FTRACK_FRAMEWORK_EXTENSIONS_PATH``).

Unlike in-DCC-python integrations (e.g. Maya) no test server is
injected into Harmony - the framework runs in a standalone Python
process spawned by Connect (``--run-framework-standalone``). In the
tests that role is played by the test process itself (tier 1,
tests/test_launch.py) or a spawned standalone process (tier 2,
tests/test_standalone.py).

Works against both a built Connect plugin directory
(``dist/ftrack-framework-harmony-<version>``) and the source project
directory.
"""

from __future__ import annotations

import importlib.util
import logging
import os
import platform
import re
import signal
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dcc_test_harness._app_discovery import (
    discover_executable,
    load_launch_config,
)
from dcc_test_harness.connect_launcher import _detect_layout
from dcc_test_harness.launcher import (
    DCCProcess,
    LaunchConfig,
    Launcher,
)

logger = logging.getLogger(__name__)

HOOK_FILENAME = "discover_ftrack_framework_harmony.py"

# Harmony's macOS process / accessibility name per edition.
_PROCESS_NAME = {
    "premium": "Harmony Premium",
    "advanced": "Harmony Advanced",
    "essentials": "Harmony Essentials",
}


def find_free_port() -> int:
    """Return a free TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _osascript(script: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
    )


def click_button_if_present(
    process_name: str, button_names: list[str]
) -> Optional[str]:
    """Click the first matching button in any window of *process_name*.

    macOS-only, via System Events accessibility. Returns the clicked
    button name, or ``None`` if none was found. Best-effort: returns
    ``None`` (with a warning) if accessibility permission is missing
    or the process has no UI yet.
    """
    if platform.system() != "Darwin":
        return None
    names_list = ", ".join(f'"{n}"' for n in button_names)
    # Activate the process first: a modal dialog on a background
    # (inactive) app is greyed out and won't accept the press.
    script = f"""
    tell application "System Events"
      if not (exists process "{process_name}") then return "no process"
      set frontmost of process "{process_name}" to true
      delay 0.5
      tell process "{process_name}"
        repeat with w in windows
          repeat with b in buttons of w
            if name of b is in {{{names_list}}} then
              perform action "AXPress" of b
              return "clicked:" & (name of b)
            end if
          end repeat
        end repeat
      end tell
    end tell
    return "not found"
    """
    result = _osascript(script)
    if result.returncode != 0:
        # -1728: not allowed assistive access; -25211: no access.
        logger.warning(
            "Accessibility click failed (grant the test runner "
            "Accessibility permission in System Settings > Privacy "
            "& Security). Detail: %s",
            result.stderr.strip(),
        )
        return None
    out = result.stdout.strip()
    if out.startswith("clicked:"):
        return out.split(":", 1)[1]
    return None


def list_windows(process_name: str) -> str:
    """Return the window titles of *process_name*, for diagnostics."""
    if platform.system() != "Darwin":
        return "<window listing only supported on macOS>"
    result = _osascript(
        f'tell application "System Events" to tell process '
        f'"{process_name}" to get name of every window'
    )
    return (result.stdout or result.stderr).strip()


def find_harmony_pid(process_name: str) -> Optional[int]:
    """Return the PID of the running Harmony process, if any."""
    result = subprocess.run(
        ["pgrep", "-f", f"MacOS/{process_name}"],
        capture_output=True,
        text=True,
    )
    pids = [int(p) for p in result.stdout.split() if p.strip()]
    return pids[0] if pids else None


def assert_no_running_harmony() -> None:
    """Fail when a Harmony instance is already running.

    A second Harmony instance fails its FlexNet license check
    ("Licensing Error ... Internal Error - Please report to
    Flexera"), so tests must not launch next to an existing session
    (a real user session or orphans from earlier test runs).
    """
    if platform.system() == "Windows":
        # pgrep-based guard not implemented on Windows.
        return
    result = subprocess.run(
        ["pgrep", "-fl", r"Harmony (Premium|Advanced|Essentials)"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        raise RuntimeError(
            "Harmony is already running - a second instance would "
            "fail its license check. Close Harmony (or kill stale "
            "test processes) and re-run.\n"
            f"Running processes:\n{result.stdout}"
        )


@dataclass
class HarmonyProcess(DCCProcess):
    """A running Harmony process with the ftrack JS package loaded.

    ``port`` is the RPC server port (the port the standalone framework
    process - or the test playing its role - listens on, and Harmony's
    JS package dials out to).

    Launched via macOS ``open`` (LaunchServices) so Harmony resolves
    its license from the app bundle context, exactly as ftrack
    Connect does. ``open`` detaches the app under launchd, so the
    process is tracked by PID rather than a ``Popen`` handle
    (``process`` is the short-lived ``open`` invocation).
    """

    session_id: str = ""
    app_version: str = ""
    env: dict = field(default_factory=dict)
    harmony_pid: int = 0
    process_name: str = "Harmony Premium"

    def is_alive(self) -> bool:
        if not self.harmony_pid:
            return False
        try:
            os.kill(self.harmony_pid, 0)
            return True
        except OSError:
            return False

    def describe_windows(self) -> str:
        """Current window titles, to diagnose a stuck dialog."""
        return list_windows(self.process_name)

    def quit(self, timeout: float = 20.0) -> None:
        """Quit Harmony gracefully, as a user closing the app would.

        Simulates a *clean* exit (distinct from ``terminate()``'s
        SIGKILL crash): asks the app to quit via LaunchServices
        (``osascript ... to quit``) on macOS, or SIGTERM elsewhere, then
        SIGKILL-sweeps anything still lingering so the next launch's
        license check is not broken.
        """
        if platform.system() == "Darwin":
            _osascript(f'tell application "{self.process_name}" to quit')
        elif self.harmony_pid:
            try:
                os.kill(self.harmony_pid, signal.SIGTERM)
            except OSError:
                pass

        deadline = time.monotonic() + timeout
        while self.is_alive() and time.monotonic() < deadline:
            time.sleep(0.2)

        # Ensure a clean slate for subsequent launches even if the
        # graceful quit stalled (e.g. an unsaved-changes prompt).
        if self.is_alive():
            logger.warning(
                "Harmony (pid=%d) did not quit gracefully, forcing.",
                self.harmony_pid,
            )
            self.terminate()

    def terminate(self, timeout: float = 10.0) -> None:
        """Kill Harmony and any helper processes it forked.

        Harmony spawns children (licensing helpers etc.); leftover
        instances break the license check of subsequent launches, so
        the whole tree is cleared.
        """
        if self.harmony_pid:
            try:
                os.kill(self.harmony_pid, signal.SIGKILL)
            except OSError:
                pass
        # Sweep any stragglers (helpers, extra instances).
        subprocess.run(
            ["pkill", "-9", "-f", f"MacOS/{self.process_name}"],
            capture_output=True,
        )
        deadline = time.monotonic() + timeout
        while self.is_alive() and time.monotonic() < deadline:
            time.sleep(0.2)
        if self.is_alive():
            logger.warning(
                "Harmony (pid=%d) did not exit after SIGKILL",
                self.harmony_pid,
            )


class HarmonyLauncher(Launcher):
    """Launch Harmony using the ftrack Connect plugin configuration."""

    def __init__(
        self,
        connect_plugin_path: str,
        variant: str = "premium",
        dcc_version: Optional[str] = None,
    ) -> None:
        self._plugin_path = Path(connect_plugin_path).resolve()
        if not self._plugin_path.is_dir():
            raise FileNotFoundError(
                f"Connect plugin path does not exist: {connect_plugin_path}"
            )
        self._variant = variant
        self._dcc_version = dcc_version
        self._layout = _detect_layout(self._plugin_path)
        self._launch_config = load_launch_config(
            self._require_file(
                self._layout.launch_dir / f"harmony-launch-{variant}.yaml"
            )
        )
        self._hook = self._load_hook_module()
        self._discovered_version: Optional[str] = None

    @property
    def is_built_layout(self) -> bool:
        """True when pointed at a built plugin, not the source tree."""
        return (self._plugin_path / "launch").is_dir()

    @staticmethod
    def _require_file(path: Path) -> Path:
        if not path.is_file():
            raise FileNotFoundError(f"Missing file: {path}")
        return path

    def _load_hook_module(self):
        """Import the connect-plugin hook module by path.

        Gives the tests the exact ``sync_js_plugin`` deployment logic
        Connect runs at launch.
        """
        if self.is_built_layout:
            hook_file = self._plugin_path / "hook" / HOOK_FILENAME
        else:
            hook_file = (
                self._plugin_path / "connect-plugin" / "hook" / HOOK_FILENAME
            )
        self._require_file(hook_file)
        spec = importlib.util.spec_from_file_location(
            "harmony_connect_hook", hook_file
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def extensions_paths(self) -> list[str]:
        """Framework extensions paths, mirroring what Connect resolves
        from the launch config's ``extensions_path`` entries."""
        paths = []
        if self.is_built_layout:
            candidates = [
                self._plugin_path / "extensions" / "common",
                self._plugin_path / "extensions" / "harmony",
            ]
        else:
            candidates = [
                self._plugin_path.parent / "framework-common-extensions",
                self._plugin_path / "extensions",
            ]
        for candidate in candidates:
            if candidate.is_dir():
                paths.append(str(candidate))
        return paths

    def _resolve_version(self, app_path: str) -> str:
        """Major Harmony version, as the hook derives it."""
        if self._discovered_version:
            return self._discovered_version.split(".")[0]
        for part in Path(app_path).parts:
            if part.lower().startswith("toon boom"):
                match = re.search(r"\d+", part)
                if match:
                    return match.group(0)
        raise FileNotFoundError(
            f"Could not determine Harmony version from path: {app_path}"
        )

    def launch(self, config: LaunchConfig) -> HarmonyProcess:
        """Start Harmony with the ftrack integration environment."""
        assert_no_running_harmony()

        # 1. Find the executable via the launch config search paths.
        if config.dcc_executable:
            app_path = config.dcc_executable
        else:
            app = discover_executable(
                self._launch_config, version=self._dcc_version
            )
            app_path = app.path
            self._discovered_version = app.version

        version = self._resolve_version(app_path)
        process_name = _PROCESS_NAME.get(self._variant, "Harmony Premium")

        # 2. Deploy the ftrack JS package exactly like the hook does
        #    on launch.
        self._hook.sync_js_plugin(
            app_path,
            [],
            bootstrap_path=str(self._layout.bootstrap_dir),
        )

        # 3. Build the Connect-equivalent environment.
        port = find_free_port()
        session_id = str(uuid.uuid4())

        env = self._build_env(config)
        env.pop("PYTHONHOME", None)

        prepend = []
        if self._layout.dependencies_dir.is_dir():
            prepend.append(str(self._layout.dependencies_dir))
        source_dir = self._plugin_path / "source"
        if not self.is_built_layout and source_dir.is_dir():
            prepend.append(str(source_dir))
        if self._layout.bootstrap_dir.is_dir():
            prepend.append(str(self._layout.bootstrap_dir))
        if prepend:
            existing = env.get("PYTHONPATH", "")
            joined = os.pathsep.join(prepend)
            env["PYTHONPATH"] = (
                joined + os.pathsep + existing if existing else joined
            )

        env["FTRACK_INTEGRATION_LISTEN_PORT"] = str(port)
        env["FTRACK_REMOTE_INTEGRATION_SESSION_ID"] = session_id
        env["FTRACK_HARMONY_VERSION"] = version

        extensions_paths = self.extensions_paths()
        if extensions_paths:
            env["FTRACK_FRAMEWORK_EXTENSIONS_PATH"] = os.pathsep.join(
                extensions_paths
            )

        # 4. Launch via macOS `open` (LaunchServices), exactly as
        #    ftrack Connect does on macOS. This is required so
        #    Harmony resolves its license from the app-bundle context
        #    - launching the raw binary fails the FlexNet check. `open`
        #    with a custom environment propagates our FTRACK_* vars to
        #    the app.
        logger.info(
            "Launching Harmony %s (%s) with ftrack JS server port %s",
            version,
            app_path,
            port,
        )
        open_proc = subprocess.Popen(
            ["open", "-n", app_path],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # 5. Find the detached Harmony process (open exits immediately;
        #    the app runs under launchd).
        harmony_pid = None
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            harmony_pid = find_harmony_pid(process_name)
            if harmony_pid:
                break
            time.sleep(0.5)
        if not harmony_pid:
            raise RuntimeError(
                f"Harmony process ({process_name}) did not appear "
                f"after `open`. `open` exit code: "
                f"{open_proc.poll()}"
            )

        # 6. Dismiss the trial dialog ("Continue Trial"). On a
        #    licensed install this dialog is absent and this is a
        #    no-op. The package's TCP server only comes up after the
        #    dialog is dismissed, so poll+click until it's gone.
        self._dismiss_trial_dialog(process_name, config)

        return HarmonyProcess(
            process=open_proc,
            port=port,
            host="127.0.0.1",
            session_id=session_id,
            app_version=version,
            env=env,
            harmony_pid=harmony_pid,
            process_name=process_name,
        )

    def create_new_scene(
        self,
        harmony_process: "HarmonyProcess",
        scene_name: Optional[str] = None,
        timeout: float = 60.0,
    ) -> Optional[Path]:
        """Create and open a new scene via File > New (accessibility).

        Harmony's main window stays inactive - and the ftrack JS
        package's TCP server never comes up - until a scene is open.
        Connect itself does not create a scene (a human does), so this
        is a test-only step. A future improvement is opening a
        committed scene fixture via File > Open instead.

        Returns the created scene directory (for teardown cleanup),
        or ``None`` on non-macOS platforms.
        """
        if platform.system() != "Darwin":
            return None
        scene_name = scene_name or f"ftrack_test_{os.getpid()}"
        process_name = harmony_process.process_name

        # Open File > New... (retry until the dialog appears).
        deadline = time.monotonic() + timeout
        dialog_up = False
        while time.monotonic() < deadline:
            _osascript(
                f'tell application "System Events" to tell process '
                f'"{process_name}"\n'
                f"  set frontmost to true\n"
                f"  delay 0.3\n"
                f"  try\n"
                f'    click menu item "New..." of menu 1 of menu '
                f'bar item "File" of menu bar 1\n'
                f"  end try\n"
                f"end tell"
            )
            time.sleep(2)
            res = _osascript(
                f'tell application "System Events" to tell process '
                f'"{process_name}" to return (exists window '
                f'"New Scene")'
            )
            if res.stdout.strip() == "true":
                dialog_up = True
                break
        if not dialog_up:
            raise RuntimeError(
                "New Scene dialog did not appear. Windows: "
                f"{list_windows(process_name)}"
            )

        # Set the scene name and click Create.
        result = _osascript(
            f'tell application "System Events" to tell process '
            f'"{process_name}"\n'
            f"  set frontmost to true\n"
            f'  set value of text field 1 of window "New Scene" '
            f'to "{scene_name}"\n'
            f"  delay 0.3\n"
            f'  click button "Create" of window "New Scene"\n'
            f"end tell"
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to create scene: {result.stderr.strip()}"
            )
        logger.info("Created Harmony scene %r", scene_name)
        # Default offline scene location.
        return Path.home() / "Documents" / "harmony" / scene_name

    def _dismiss_trial_dialog(
        self, process_name: str, config: LaunchConfig
    ) -> None:
        """Poll for and click the trial dialog's "Continue Trial".

        Best-effort and macOS-only; a licensed install shows no
        dialog. Logs (but does not fail) if accessibility permission
        is missing - the JS server simply never comes up and the
        connecting test surfaces a clear timeout.
        """
        if platform.system() != "Darwin":
            return
        deadline = time.monotonic() + min(config.startup_timeout, 90)
        while time.monotonic() < deadline:
            clicked = click_button_if_present(process_name, ["Continue Trial"])
            if clicked:
                logger.info("Dismissed trial dialog (%s)", clicked)
                return
            time.sleep(2)
        logger.info(
            "No trial dialog dismissed (licensed install, or "
            "accessibility permission not granted)."
        )

    def spawn_standalone(
        self,
        harmony_process: HarmonyProcess,
        wrapper: Path,
        extra_env: Optional[dict] = None,
    ) -> tuple[subprocess.Popen, str]:
        """Spawn the standalone framework process for *harmony_process*.

        Mirrors Connect's ``--run-framework-standalone
        ftrack_framework_harmony`` helper spawn: same environment as
        the DCC, run with this (test) Python interpreter. *wrapper*
        is the bootstrap script to run (which injects the harness
        server before importing the integration).

        Returns the process and the path of its output log file.
        """
        env = dict(harmony_process.env)
        env.update(extra_env or {})

        log_fd, log_path = tempfile.mkstemp(
            prefix="harmony_standalone_test_", suffix=".log"
        )
        log_file = os.fdopen(log_fd, "w")

        process = subprocess.Popen(
            [sys.executable, str(wrapper)],
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
        return process, log_path
