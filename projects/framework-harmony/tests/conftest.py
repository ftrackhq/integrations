# :coding: utf-8
# :copyright: Copyright (c) 2026 ftrack

"""Test configuration for framework-harmony.

The tests launch a local Harmony installation through the same code
path ftrack Connect uses (launch config discovery + JS package
deployment + Connect environment) and verify the integration
bootstraps. They are skipped when Harmony is not installed.

Usage, from the project directory::

    uv sync --extra ftrack-libs --extra framework-libs --extra test

    # Against the source tree:
    uv run pytest tests/

    # Against a built Connect plugin (closest to production):
    uv run pytest tests/ \\
        --dcc-connect-plugin dist/ftrack-framework-harmony-<version>

tests/test_standalone.py additionally requires ftrack credentials
(``FTRACK_SERVER``/``FTRACK_API_KEY`` env vars, or a previous ftrack
Connect login) and is skipped without them.
"""

import os
import platform
import shutil
import ssl
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

import pytest

from dcc_test_harness.client import DCCClient
from dcc_test_harness.connect_launcher import resolve_ftrack_credentials
from dcc_test_harness.exceptions import DCCConnectionError
from dcc_test_harness.launcher import LaunchConfig

from _launcher import HarmonyLauncher, HarmonyProcess
from _rpc_client import HarmonyRPCTestClient

PROJECT_DIR = Path(__file__).parent.parent


def tail_file(log_path, lines=40):
    """Return the tail of a log file, for diagnostics."""
    try:
        with open(log_path, "r", errors="replace") as f:
            return "".join(f.readlines()[-lines:])
    except OSError:
        return "<no output captured>"


@pytest.fixture(scope="module")
def harmony_launcher(request):
    """Launcher configured from ``--dcc-connect-plugin``.

    Defaults to the source project directory so a plain
    ``uv run pytest tests/`` works during development.
    """
    plugins = request.config.getoption("dcc_connect_plugin") or [
        str(PROJECT_DIR)
    ]
    try:
        return HarmonyLauncher(
            plugins[0],
            dcc_version=request.config.getoption("dcc_version"),
        )
    except FileNotFoundError as error:
        pytest.skip(f"Cannot set up Harmony launcher: {error}")


@pytest.fixture(scope="module")
def harmony_process(request, harmony_launcher):
    """A running Harmony instance with the ftrack JS package deployed.

    Module-scoped: the integration holds a single client connection, so
    each test module gets its own Harmony.

    No scene is created here: Harmony only dials the RPC server once a
    scene is open, and the server (the test in tier-1, the real
    standalone in tier-2) must be listening first. The consuming fixture
    therefore starts its server and then creates the scene.
    """
    config = LaunchConfig(
        dcc_executable=request.config.getoption("dcc_executable"),
        startup_timeout=request.config.getoption("dcc_startup_timeout"),
    )
    try:
        process = harmony_launcher.launch(config)
    except FileNotFoundError as error:
        pytest.skip(f"Harmony not installed: {error}")

    yield process

    process.terminate()


@pytest.fixture(scope="module")
def harmony_connection(request, harmony_launcher, harmony_process):
    """Accepted RPC connection from Harmony, context-data handshake done.

    The test process plays the standalone framework process' server
    role: it listens on the integration port, creates a scene (so
    Harmony's JS package dials out - it only connects once a scene is
    open), accepts the connection and completes the context-data
    handshake.
    """
    client = HarmonyRPCTestClient(
        harmony_process.host,
        harmony_process.port,
        harmony_process.session_id,
    )
    scene_dir = None
    try:
        client.listen()
        # Now that the server is listening, create a scene so Harmony
        # dials out to it.
        scene_dir = harmony_launcher.create_new_scene(harmony_process)
        client.accept(
            is_alive=harmony_process.is_alive,
            timeout=request.config.getoption("dcc_startup_timeout"),
        )
        client.handshake()
    except (TimeoutError, RuntimeError, ConnectionError, OSError) as error:
        client.close()
        if scene_dir is not None:
            shutil.rmtree(scene_dir, ignore_errors=True)
        pytest.fail(
            f"Harmony integration did not come up: {error}\n"
            f"--- Harmony windows (stuck at a dialog?) ---\n"
            f"{harmony_process.describe_windows()}"
        )

    yield client

    client.close()
    if scene_dir is not None:
        shutil.rmtree(scene_dir, ignore_errors=True)


@dataclass
class StandaloneBundle:
    """A live standalone framework process + a harness client to it."""

    client: DCCClient
    process: object  # subprocess.Popen
    harmony_process: HarmonyProcess
    launcher: HarmonyLauncher
    log_path: str


@pytest.fixture(scope="module")
def standalone_bundle(request, harmony_launcher, harmony_process):
    """Spawn the real standalone framework process next to Harmony.

    Mirrors Connect's ``--run-framework-standalone`` helper: same
    environment as Harmony (incl. ``FTRACK_APPLICATION_PID`` so the
    watchdog monitors the right process) plus the ftrack credentials
    Connect injects. Skips when credentials are unavailable. Yields a
    ``StandaloneBundle`` (harness client + process handle).
    """
    credentials = resolve_ftrack_credentials()
    if credentials is None:
        pytest.skip("ftrack credentials required")

    port_file = tempfile.mktemp(prefix="harmony_standalone_", suffix=".port")
    extra_env = {
        "FTRACK_SERVER": credentials["server"],
        "FTRACK_API_KEY": credentials["api_key"],
        "FTRACK_APIKEY": credentials["api_key"],
        "FTRACK_EVENT_SERVER": credentials["server"],
        "FTRACK_APPLICATION_PID": str(harmony_process.harmony_pid),
        "DCC_TEST_PORT_FILE": port_file,
    }
    if credentials["api_user"]:
        extra_env["FTRACK_API_USER"] = credentials["api_user"]
    if platform.system() != "Windows":
        cafile = ssl.get_default_verify_paths().cafile
        if cafile:
            extra_env["SSL_CERT_FILE"] = cafile

    process, log_path = harmony_launcher.spawn_standalone(
        harmony_process,
        Path(__file__).parent / "_standalone_wrapper.py",
        extra_env=extra_env,
    )

    client = None
    scene_dir = None
    startup_timeout = request.config.getoption("dcc_startup_timeout")
    try:
        port = harmony_launcher._wait_for_port_file(
            port_file, startup_timeout, process
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

        # The standalone is now the RPC server; Harmony dials it. A
        # synchronous execute blocks until the Qt event loop runs, which
        # is only reached after bootstrap_integration() has bound the RPC
        # port - so the server is listening before we make Harmony dial.
        client.execute("__result__ = True")

        # Now that the standalone is listening, create a scene so Harmony
        # dials out to it (it only connects once a scene is open).
        scene_dir = harmony_launcher.create_new_scene(harmony_process)

        # Wait until Harmony has connected to the standalone.
        deadline = time.monotonic() + startup_timeout
        while True:
            connected = client.execute(
                "from ftrack_framework_harmony.utils import TCPRPCClient\n"
                "__result__ = ("
                "TCPRPCClient._instance is not None"
                " and TCPRPCClient._instance.connected)"
            )
            if connected:
                break
            if time.monotonic() > deadline:
                pytest.fail(
                    "Harmony never connected to the standalone process.\n"
                    f"--- standalone output tail ---\n{tail_file(log_path)}\n"
                    f"--- Harmony windows ---\n"
                    f"{harmony_process.describe_windows()}"
                )
            time.sleep(1.0)
    except BaseException:
        if client is not None:
            client.disconnect()
        process.kill()
        process.wait(timeout=10)
        if scene_dir is not None:
            shutil.rmtree(scene_dir, ignore_errors=True)
        raise
    finally:
        try:
            os.unlink(port_file)
        except OSError:
            pass

    yield StandaloneBundle(
        client=client,
        process=process,
        harmony_process=harmony_process,
        launcher=harmony_launcher,
        log_path=log_path,
    )

    # Clean shutdown: quit the Qt loop via the harness, then ensure exit.
    try:
        client.shutdown_server()
    except Exception:
        pass
    try:
        process.wait(timeout=15)
    except Exception:
        process.kill()
        process.wait(timeout=10)
    client.disconnect()
    if scene_dir is not None:
        shutil.rmtree(scene_dir, ignore_errors=True)
