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

import shutil
from pathlib import Path

import pytest

from dcc_test_harness.launcher import LaunchConfig

from _launcher import HarmonyLauncher
from _rpc_client import HarmonyRPCTestClient

PROJECT_DIR = Path(__file__).parent.parent


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

    Module-scoped: the JS TCP server holds a single client
    connection, so each test module gets its own Harmony.
    """
    config = LaunchConfig(
        dcc_executable=request.config.getoption("dcc_executable"),
        startup_timeout=request.config.getoption("dcc_startup_timeout"),
    )
    try:
        process = harmony_launcher.launch(config)
    except FileNotFoundError as error:
        pytest.skip(f"Harmony not installed: {error}")

    # The ftrack JS package's TCP server only comes up once a scene
    # is open, so create a temporary one (cleaned up on teardown).
    scene_dir = None
    try:
        scene_dir = harmony_launcher.create_new_scene(process)
    except Exception as error:
        process.terminate()
        pytest.fail(
            f"Could not create a Harmony scene: {error}\n"
            f"--- Harmony windows ---\n"
            f"{process.describe_windows()}"
        )

    yield process

    process.terminate()
    if scene_dir is not None:
        shutil.rmtree(scene_dir, ignore_errors=True)


@pytest.fixture(scope="module")
def harmony_connection(request, harmony_process):
    """Connected RPC client, context-data handshake completed.

    The test process plays the role of the standalone framework
    process here.
    """
    client = HarmonyRPCTestClient(
        harmony_process.host,
        harmony_process.port,
        harmony_process.session_id,
    )
    try:
        client.connect_with_retry(
            is_alive=harmony_process.is_alive,
            timeout=request.config.getoption("dcc_startup_timeout"),
        )
        client.handshake()
    except (TimeoutError, RuntimeError, ConnectionError) as error:
        client.close()
        pytest.fail(
            f"Harmony integration did not come up: {error}\n"
            f"--- Harmony windows (stuck at a dialog?) ---\n"
            f"{harmony_process.describe_windows()}"
        )

    yield client

    client.close()
