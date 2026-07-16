# :coding: utf-8
# :copyright: Copyright (c) 2026 ftrack

"""Frozen-Qt environment scrub: hook helper + live Harmony verification.

A frozen (PyInstaller) ftrack Connect leaks its own bundled Qt paths
(``QT_PLUGIN_PATH`` etc.) into the environment of launched DCCs. Harmony
then loads Connect's Qt plugins - built against a newer Qt minor than
Harmony's own - which prints ~10 "Plugin uses incompatible Qt library"
warnings and breaks menus/dialogs. The Harmony hook helper
``get_frozen_qt_environment_actions`` emits Connect launch-env actions
that strip those paths from the child environment.

Three groups (mirroring tests/test_launch.py / tests/test_standalone.py
gating):

* Unit cases - the hook helper's action emission, run anywhere (no DCC).
* Tier-1 live cases - a fake frozen bundle is composed exactly as Connect
  would (helper -> actions -> ``apply_env_actions`` -> ``LaunchConfig``)
  and Harmony is launched with it; the scrub is verified on the *live*
  process. Skipped when Harmony is absent.
* Tier-2 - the real standalone framework process' captured log is free of
  the Qt-loader warnings. Requires ftrack credentials.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
from pathlib import Path

import pytest

from _launcher import apply_env_actions
from _rpc_client import HarmonyRPCTestClient

from dcc_test_harness.launcher import LaunchConfig

HOOK_PATH = (
    Path(__file__).parent.parent
    / "connect-plugin"
    / "hook"
    / "discover_ftrack_framework_harmony.py"
)


@pytest.fixture(scope="module")
def hook():
    """The connect-plugin hook module, loaded from the source tree.

    Mirrors ``_launcher._load_hook_module``; gives the tests the exact
    ``get_frozen_qt_environment_actions`` Connect runs at launch.
    """
    spec = importlib.util.spec_from_file_location(
        "harmony_hook_under_test", HOOK_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# Unit cases - action emission, no DCC.
# ---------------------------------------------------------------------------


def test_not_frozen_returns_no_actions(hook):
    """Not frozen (no bundle roots) -> no env actions at all."""
    leaked = {"QT_PLUGIN_PATH": os.path.normpath("/anything/PySide6/plugins")}
    assert (
        hook.get_frozen_qt_environment_actions(environ=leaked, bundle_roots=[])
        == {}
    )


def test_bundle_only_emits_unset(hook):
    """A var holding only bundle entries -> ``.unset``."""
    root = os.path.normpath("/opt/connect/_internal")
    leaked = {"QT_PLUGIN_PATH": os.path.join(root, "PySide6", "plugins")}

    actions = hook.get_frozen_qt_environment_actions(
        environ=leaked, bundle_roots=[root]
    )

    assert actions == {"QT_PLUGIN_PATH.unset": "1"}


def test_mixed_emits_set_with_foreign_remainder(hook):
    """A mixed var -> ``.set`` with only the studio entries, in order."""
    root = os.path.normpath("/opt/connect/_internal")
    studio_a = os.path.normpath("/studio/qt/a/plugins")
    studio_b = os.path.normpath("/studio/qt/b/plugins")
    bundle = os.path.join(root, "PySide6", "plugins")
    leaked = {"QT_PLUGIN_PATH": os.pathsep.join([studio_a, bundle, studio_b])}

    actions = hook.get_frozen_qt_environment_actions(
        environ=leaked, bundle_roots=[root]
    )

    assert actions == {
        "QT_PLUGIN_PATH.set": os.pathsep.join([studio_a, studio_b])
    }


def test_studio_only_emits_no_action(hook):
    """Nothing under a bundle root -> the studio value is left alone."""
    root = os.path.normpath("/opt/connect/_internal")
    leaked = {"QML2_IMPORT_PATH": os.path.normpath("/studio/qml")}

    assert (
        hook.get_frozen_qt_environment_actions(
            environ=leaked, bundle_roots=[root]
        )
        == {}
    )


def test_absent_var_emits_no_action(hook):
    """A var not present in the environment yields no action."""
    root = os.path.normpath("/opt/connect/_internal")

    assert (
        hook.get_frozen_qt_environment_actions(environ={}, bundle_roots=[root])
        == {}
    )


def test_only_qt_vars_are_scoped(hook):
    """PATH / loader paths are out of scope for the transitional hook."""
    root = os.path.normpath("/opt/connect/_internal")
    leaked = {
        "PATH": os.path.join(root, "bin"),
        "LD_LIBRARY_PATH": os.path.join(root, "lib"),
        "QT_PLUGIN_PATH": os.path.join(root, "plugins"),
    }

    actions = hook.get_frozen_qt_environment_actions(
        environ=leaked, bundle_roots=[root]
    )

    assert actions == {"QT_PLUGIN_PATH.unset": "1"}


def test_macos_two_roots(hook):
    """macOS: entries under both _MEIPASS and the .app root are stripped."""
    app_root = os.path.normpath("/Applications/Ftrack Connect.app")
    meipass = os.path.join(app_root, "Contents", "Frameworks")
    frameworks_qml = os.path.join(meipass, "PySide6", "Qt", "qml")
    resources_qml = os.path.join(app_root, "Contents", "Resources", "qml")
    studio = os.path.normpath("/studio/qml")
    leaked = {
        "QML2_IMPORT_PATH": os.pathsep.join(
            [frameworks_qml, resources_qml, studio]
        )
    }

    actions = hook.get_frozen_qt_environment_actions(
        environ=leaked, bundle_roots=[meipass, app_root]
    )

    assert actions == {"QML2_IMPORT_PATH.set": studio}


def test_on_launch_integration_merges_actions(hook, tmp_path, monkeypatch):
    """``on_launch_integration`` injects the scrub actions into the env.

    Simulates a frozen Connect (``sys.frozen`` + ``sys._MEIPASS``) whose
    process environment carries a leaked ``QT_PLUGIN_PATH`` under the
    bundle, and asserts the launch handler emits the corresponding
    ``.unset`` action alongside its normal launch env.
    """
    meipass = tmp_path / "_internal"
    (meipass / "PySide6" / "plugins").mkdir(parents=True)

    monkeypatch.setattr(hook.sys, "frozen", True, raising=False)
    monkeypatch.setattr(hook.sys, "_MEIPASS", str(meipass), raising=False)
    monkeypatch.setenv("QT_PLUGIN_PATH", str(meipass / "PySide6" / "plugins"))

    # Do not touch the real Harmony scripts folder or bundled scene.
    monkeypatch.setattr(
        hook,
        "sync_js_plugin",
        lambda *args, **kwargs: "/tmp/fake/packages/ftrack",
    )

    event = {
        "data": {
            "integration": {},
            "application": {
                "version": "25",
                "path": "/Applications/Toon Boom Harmony 25 Premium/x",
                "environment_variables": {
                    "FTRACK_FRAMEWORK_EXTENSIONS_PATH": "",
                    # Keep the welcome/staging screen so no scene is staged.
                    "FTRACK_HARMONY_LAUNCH_INTO_SCENE": "0",
                },
            },
            "context": {"selection": []},
        }
    }

    launch_data = hook.on_launch_integration(session=None, event=event)

    env = launch_data["integration"]["env"]
    assert env.get("QT_PLUGIN_PATH.unset") == "1"


def test_on_launch_integration_preserves_configured_actions(
    hook, tmp_path, monkeypatch
):
    """A studio's own configured Qt action survives and wins over the scrub.

    Connect applies env actions in dict insertion order, so a scrub
    ``.unset`` must be inserted *before* any pre-existing configured
    action on the same variable: the leak is removed first, then the
    studio's own ``.set``/``.prepend``/``.append`` re-applies and takes
    precedence.
    """
    meipass = tmp_path / "_internal"
    (meipass / "PySide6" / "plugins").mkdir(parents=True)
    leaked = str(meipass / "PySide6" / "plugins")

    monkeypatch.setattr(hook.sys, "frozen", True, raising=False)
    monkeypatch.setattr(hook.sys, "_MEIPASS", str(meipass), raising=False)
    # Every scrubbed var is fully bundle-owned, so each emits a ``.unset``.
    monkeypatch.setenv("QT_PLUGIN_PATH", leaked)
    monkeypatch.setenv("QML_IMPORT_PATH", leaked)
    monkeypatch.setenv("QML2_IMPORT_PATH", leaked)

    monkeypatch.setattr(
        hook,
        "sync_js_plugin",
        lambda *args, **kwargs: "/tmp/fake/packages/ftrack",
    )

    # Configured actions already on the integration (one of each kind).
    configured = {
        "QT_PLUGIN_PATH.prepend": "/studio/prepend",
        "QML_IMPORT_PATH.set": "/studio/set",
        "QML2_IMPORT_PATH.append": "/studio/append",
    }
    event = {
        "data": {
            "integration": {"env": dict(configured)},
            "application": {
                "version": "25",
                "path": "/Applications/Toon Boom Harmony 25 Premium/x",
                "environment_variables": {
                    "FTRACK_FRAMEWORK_EXTENSIONS_PATH": "",
                    "FTRACK_HARMONY_LAUNCH_INTO_SCENE": "0",
                },
            },
            "context": {"selection": []},
        }
    }

    launch_data = hook.on_launch_integration(session=None, event=event)

    env = launch_data["integration"]["env"]
    keys = list(env.keys())
    for action_key, value in configured.items():
        var = action_key.split(".")[0]
        # The configured action is preserved untouched ...
        assert env[action_key] == value
        # ... and applied after the scrub's ``.unset`` for the same var.
        assert keys.index("{}.unset".format(var)) < keys.index(action_key)


# ---------------------------------------------------------------------------
# Live-launch helpers.
# ---------------------------------------------------------------------------

# A studio-set Qt path (foreign to the fake bundle) that must survive the
# scrub - name it distinctively so it is unambiguous in the live env dump.
_STUDIO_MARKER = "ftrack_studio_qt_marker"


def _fake_frozen_bundle(base: Path):
    """Create a fake frozen-Connect bundle + a studio Qt dir under *base*.

    Returns ``(bundle_root, studio_dir)``. The bundle root plays
    ``sys._MEIPASS``; the studio dir is the foreign entry that must be
    preserved.
    """
    bundle_root = base / "_internal"
    (bundle_root / "PySide6" / "plugins").mkdir(parents=True)
    studio_dir = base / _STUDIO_MARKER
    studio_dir.mkdir(parents=True)
    return bundle_root, studio_dir


def _leaked_qt_plugin_path(bundle_root: Path, studio_dir: Path) -> str:
    """A QT_PLUGIN_PATH value mixing a bundle entry and a studio entry."""
    return os.pathsep.join(
        [str(bundle_root / "PySide6" / "plugins"), str(studio_dir)]
    )


def _launch_config(request, extra_env):
    return LaunchConfig(
        dcc_executable=request.config.getoption("dcc_executable"),
        startup_timeout=request.config.getoption("dcc_startup_timeout"),
        extra_env=extra_env,
    )


# ---------------------------------------------------------------------------
# Tier-1 control - proves the plumbing detects an *unscrubbed* leak.
# Defined before the scrubbed cases so its own Harmony is torn down before
# the module-scoped scrubbed instance is launched (only one Harmony may run
# at a time - see assert_no_running_harmony).
# ---------------------------------------------------------------------------


def test_control_unscrubbed_leak_reaches_harmony(
    request, harmony_launcher, tmp_path
):
    """Baseline: injecting the leak *without* applying the scrub actions
    leaves the bundle path in the live Harmony environment.

    Without this control a broken scrub (one that silently stripped
    nothing, or a test that asserted against the wrong process) would
    still pass. Proves the tier-1 assertions can actually fail.
    """
    bundle_root, studio_dir = _fake_frozen_bundle(tmp_path)
    leaked_env = {
        "QT_PLUGIN_PATH": _leaked_qt_plugin_path(bundle_root, studio_dir)
    }

    try:
        process = harmony_launcher.launch(_launch_config(request, leaked_env))
    except FileNotFoundError as error:
        pytest.skip(f"Harmony not installed: {error}")

    try:
        ps_env = subprocess.run(
            ["ps", "eww", str(process.harmony_pid)],
            capture_output=True,
            text=True,
        ).stdout
        assert str(bundle_root) in ps_env, (
            "Control launch: the injected bundle path did not reach the "
            "live Harmony environment, so the tier-1 scrub assertions "
            "would be vacuous.\n" + ps_env
        )
    finally:
        process.terminate()


# ---------------------------------------------------------------------------
# Tier-1 live - the scrub verified on the real Harmony process.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def scrubbed_harmony(request, harmony_launcher, tmp_path_factory):
    """Launch Harmony with a Connect-equivalent *scrubbed* environment.

    Composes the pieces exactly as Connect does: the leaked frozen-Qt
    value -> the hook's ``get_frozen_qt_environment_actions`` ->
    ``apply_env_actions`` -> ``LaunchConfig.extra_env``. Yields
    ``(process, bundle_root, studio_dir)``.
    """
    base = tmp_path_factory.mktemp("qt_env_scrub")
    bundle_root, studio_dir = _fake_frozen_bundle(base)

    leaked_env = {
        "QT_PLUGIN_PATH": _leaked_qt_plugin_path(bundle_root, studio_dir)
    }
    actions = harmony_launcher._hook.get_frozen_qt_environment_actions(
        environ=leaked_env, bundle_roots=[str(bundle_root)]
    )
    # Sanity: a mixed value must produce a ``.set`` keeping the studio
    # entry (else the fixture is not exercising what we think).
    assert actions == {"QT_PLUGIN_PATH.set": str(studio_dir)}

    # Apply the actions to the base (leaked) env, as Connect's launcher
    # would, and hand the result to the launch.
    scrubbed = apply_env_actions(dict(leaked_env), actions)

    try:
        process = harmony_launcher.launch(_launch_config(request, scrubbed))
    except FileNotFoundError as error:
        pytest.skip(f"Harmony not installed: {error}")

    yield process, bundle_root, studio_dir

    process.terminate()


def test_scrubbed_env_dict(scrubbed_harmony):
    """The launched process' env dict holds no bundle entry; studio kept."""
    process, bundle_root, studio_dir = scrubbed_harmony

    assert process.env.get("QT_PLUGIN_PATH") == str(studio_dir)
    leaked = [
        f"{key}={value}"
        for key, value in process.env.items()
        if str(bundle_root) in str(value)
    ]
    assert not leaked, f"Bundle paths leaked into the env dict: {leaked}"


def test_scrubbed_live_process(scrubbed_harmony):
    """Live-process truth via ``ps eww`` (catches open/launchd quirks the
    env dict alone would miss)."""
    process, bundle_root, studio_dir = scrubbed_harmony

    ps_env = subprocess.run(
        ["ps", "eww", str(process.harmony_pid)],
        capture_output=True,
        text=True,
    ).stdout

    assert str(bundle_root) not in ps_env, (
        "Bundle path present in the live Harmony environment:\n" + ps_env
    )
    assert _STUDIO_MARKER in ps_env, (
        "Studio Qt entry did not survive the scrub:\n" + ps_env
    )


def test_integration_bootstraps_with_scrubbed_env(
    request, harmony_launcher, scrubbed_harmony
):
    """The integration still bootstraps under the scrubbed env.

    Reuses the tier-1 connectivity assertion: Harmony's JS package dials
    in to the test's RPC port and completes the context-data handshake.
    """
    process, _bundle_root, _studio_dir = scrubbed_harmony
    client = HarmonyRPCTestClient(
        process.host, process.port, process.session_id
    )
    scene_dir = None
    try:
        client.listen()
        scene_dir = harmony_launcher.create_new_scene(process)
        client.accept(
            is_alive=process.is_alive,
            timeout=request.config.getoption("dcc_startup_timeout"),
        )
        reply = client.handshake()
    except (TimeoutError, RuntimeError, ConnectionError, OSError) as error:
        pytest.fail(
            f"Harmony integration did not come up under the scrubbed "
            f"env: {error}\n--- Harmony windows ---\n"
            f"{process.describe_windows()}"
        )
    finally:
        client.close()
        if scene_dir is not None:
            import shutil

            shutil.rmtree(scene_dir, ignore_errors=True)

    assert reply is not None
    assert reply["data"]["integration_session_id"] == process.session_id


# ---------------------------------------------------------------------------
# Tier-2 - the real standalone framework process (credentials required).
#
# Spawned next to the *same* scrubbed Harmony instance (only one Harmony may
# run at a time), so this reuses ``scrubbed_harmony`` rather than conftest's
# ``standalone_bundle`` (which would launch a second Harmony).
# ---------------------------------------------------------------------------

_FORBIDDEN_LOG_MARKERS = (
    "qt.core.plugin.loader",
    "incompatible Qt library",
)


def test_standalone_starts_with_clean_qt_log(
    request, harmony_launcher, scrubbed_harmony, tmp_path
):
    """The standalone framework process comes up with a clean Qt log.

    Mirrors Connect's ``--run-framework-standalone`` spawn with the
    already-scrubbed environment: waits for the standalone's harness
    server to bind (proves its Qt platform plugin loaded - an
    incompatible bundled plugin would abort before this) and asserts the
    captured log is free of the "incompatible Qt library" / plugin-loader
    warnings.
    """
    import platform
    import ssl
    import time

    from dcc_test_harness.client import DCCClient
    from dcc_test_harness.connect_launcher import resolve_ftrack_credentials
    from dcc_test_harness.exceptions import DCCConnectionError

    credentials = resolve_ftrack_credentials()
    if credentials is None:
        pytest.skip("ftrack credentials required")

    process, _bundle_root, _studio_dir = scrubbed_harmony

    port_file = str(tmp_path / "harmony_qt_scrub.port")
    extra_env = {
        "FTRACK_SERVER": credentials["server"],
        "FTRACK_API_KEY": credentials["api_key"],
        "FTRACK_APIKEY": credentials["api_key"],
        "FTRACK_EVENT_SERVER": credentials["server"],
        "FTRACK_APPLICATION_PID": str(process.harmony_pid),
        "DCC_TEST_PORT_FILE": port_file,
    }
    if credentials["api_user"]:
        extra_env["FTRACK_API_USER"] = credentials["api_user"]
    if platform.system() != "Windows":
        cafile = ssl.get_default_verify_paths().cafile
        if cafile:
            extra_env["SSL_CERT_FILE"] = cafile

    standalone, log_path = harmony_launcher.spawn_standalone(
        process,
        Path(__file__).parent / "_standalone_wrapper.py",
        extra_env=extra_env,
    )

    startup_timeout = request.config.getoption("dcc_startup_timeout")
    client = None
    try:
        # The port file appears only once the standalone has created its
        # QApplication and bound the harness server: proof its Qt loaded.
        port = harmony_launcher._wait_for_port_file(
            port_file, startup_timeout, standalone
        )
        client = DCCClient(host="127.0.0.1", port=port, timeout=60.0)
        deadline = time.monotonic() + 30
        while True:
            try:
                client.connect()
                break
            except (DCCConnectionError, ConnectionRefusedError):
                if time.monotonic() > deadline:
                    raise
                time.sleep(0.5)
        assert client.execute("__result__ = True") is True
    finally:
        if client is not None:
            try:
                client.shutdown_server()
            except Exception:
                pass
            client.disconnect()
        try:
            standalone.wait(timeout=15)
        except Exception:
            standalone.kill()
            standalone.wait(timeout=10)
        with open(log_path, "r", errors="replace") as handle:
            log = handle.read()
        try:
            os.unlink(port_file)
        except OSError:
            pass

    offending = [
        line
        for line in log.splitlines()
        if any(marker in line for marker in _FORBIDDEN_LOG_MARKERS)
    ]
    assert not offending, (
        "Standalone log contains Qt-loader warnings:\n" + "\n".join(offending)
    )
