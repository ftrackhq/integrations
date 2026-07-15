"""pytest fixtures for the DCC test harness.

Provides generic fixtures for connecting to a DCC application.
DCC-specific fixtures (e.g. scene reset, geometry creation)
should be defined in the integration project's conftest.py.
"""

from __future__ import annotations

import subprocess
import time
from typing import Generator, Optional

import pytest

from dcc_test_harness.client import DCCClient
from dcc_test_harness.exceptions import DCCConnectionError
from dcc_test_harness.launcher import DCCProcess, Launcher
from dcc_test_harness.qt_helpers import DCCUI


@pytest.fixture(scope="session")
def dcc_launcher(
    request: pytest.FixtureRequest,
) -> Launcher:
    """Default launcher using ftrack-connect configs.

    Uses ``--dcc-connect-plugin`` to create a
    ``ConnectLauncher``.  The DCC type is auto-detected from
    the plugin's YAML launch config, or overridden with
    ``--dcc-app``.

    When multiple ``--dcc-connect-plugin`` paths are given,
    the first is the primary plugin (provides DCC discovery
    and launch config).  Additional plugins layer their
    environment on top (PYTHONPATH, script paths, etc.).

    Override this fixture in your project's ``conftest.py``
    to use a custom ``Launcher`` subclass instead.
    """
    plugins = request.config.getoption("dcc_connect_plugin") or []

    if not plugins:
        raise pytest.UsageError(
            "No dcc_launcher fixture found and "
            "--dcc-connect-plugin not specified. Either:\n"
            "  1. Pass --dcc-connect-plugin <path>\n"
            "  2. Define a dcc_launcher fixture in your "
            "conftest.py"
        )

    primary = plugins[0]
    extra = plugins[1:]

    dcc_app = request.config.getoption("dcc_app")
    dcc_version = request.config.getoption("dcc_version")

    from dcc_test_harness.connect_launcher import (
        ConnectLauncher,
    )

    return ConnectLauncher(
        connect_plugin_path=primary,
        extra_plugins=extra,
        dcc_app=dcc_app,
        dcc_version=dcc_version,
    )


@pytest.fixture(scope="session")
def dcc_process(
    request: pytest.FixtureRequest,
    dcc_launcher: Launcher,
) -> Generator[Optional[DCCProcess], None, None]:
    """Session-scoped fixture that launches the DCC.

    Yields a ``DCCProcess`` when ``--dcc-launch`` is true
    (default), or ``None`` when connecting to an existing
    instance via ``--dcc-no-launch``.
    """
    if not request.config.getoption("dcc_launch"):
        yield None
        return

    from dcc_test_harness.launcher import LaunchConfig

    config = LaunchConfig(
        server_port=request.config.getoption("dcc_port"),
        dcc_executable=request.config.getoption("dcc_executable"),
        startup_timeout=request.config.getoption("dcc_startup_timeout"),
    )

    process = dcc_launcher.launch(config)

    yield process

    # Teardown: wait for DCC to exit cleanly (quit_fn triggered
    # by shutdown_server in dcc_client teardown), fallback to kill.
    try:
        process.process.wait(timeout=15.0)
    except subprocess.TimeoutExpired:
        process.terminate()


@pytest.fixture(scope="session")
def dcc_client(
    request: pytest.FixtureRequest,
    dcc_process: Optional[DCCProcess],
) -> Generator[DCCClient, None, None]:
    """Session-scoped connection to a running DCC instance.

    Automatically connects using the port from ``dcc_process``
    (if launched) or from ``--dcc-host`` / ``--dcc-port``.
    """
    if dcc_process is not None:
        host = dcc_process.host
        port = dcc_process.port
    else:
        host = request.config.getoption("dcc_host")
        port = request.config.getoption("dcc_port")
        if port == 0:
            raise pytest.UsageError(
                "--dcc-port is required when using --dcc-no-launch"
            )

    timeout = request.config.getoption("dcc_timeout")
    startup_timeout = request.config.getoption("dcc_startup_timeout")

    client = DCCClient(host=host, port=port, timeout=timeout)

    deadline = time.monotonic() + startup_timeout
    last_error: Optional[Exception] = None
    while time.monotonic() < deadline:
        try:
            client.connect()
            break
        except (DCCConnectionError, OSError) as e:
            last_error = e
            time.sleep(0.5)
    else:
        raise DCCConnectionError(
            f"Could not connect to DCC at {host}:{port} "
            f"within {startup_timeout}s: {last_error}"
        )

    yield client

    try:
        if dcc_process is not None:
            client.shutdown_server()
    finally:
        client.disconnect()


@pytest.fixture(scope="session")
def dcc_ui(dcc_client: DCCClient) -> DCCUI:
    """Session-scoped UI interaction helper."""
    return DCCUI(dcc_client)
