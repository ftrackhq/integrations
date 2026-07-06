"""pytest plugin for the DCC test harness.

Auto-discovered via the ``pytest11`` entry point in pyproject.toml.
Registers CLI options and generic fixtures.
"""

from __future__ import annotations

import pytest

from dcc_test_harness.fixtures import (  # noqa: F401
    dcc_client,
    dcc_launcher,
    dcc_process,
    dcc_ui,
)


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("dcc", "DCC test harness options")
    group.addoption(
        "--dcc-launch",
        action="store_true",
        default=True,
        dest="dcc_launch",
        help=("Auto-launch DCC with the test server (default: true)"),
    )
    group.addoption(
        "--dcc-no-launch",
        action="store_false",
        dest="dcc_launch",
        help=("Do not launch DCC; connect to an already-running instance"),
    )
    group.addoption(
        "--dcc-connect-plugin",
        action="append",
        default=[],
        dest="dcc_connect_plugin",
        help=(
            "Path to a built ftrack connect plugin "
            "directory or source project. Can be "
            "specified multiple times; the first is "
            "the primary plugin (provides DCC "
            "discovery), additional plugins layer "
            "their environment on top."
        ),
    )
    group.addoption(
        "--dcc-app",
        default=None,
        help=(
            "Override DCC type (e.g. maya, nuke). "
            "Normally auto-detected from the connect "
            "plugin's launch config."
        ),
    )
    group.addoption(
        "--dcc-version",
        default=None,
        help=(
            "DCC version to use (e.g. 2025, 2026). "
            "Prefix-matched against discovered versions. "
            "Defaults to the newest installed version."
        ),
    )
    group.addoption(
        "--dcc-executable",
        default=None,
        help="Path to the DCC executable (auto-detected if omitted)",
    )
    group.addoption(
        "--dcc-host",
        default="127.0.0.1",
        help="DCC RPC server host (default: 127.0.0.1)",
    )
    group.addoption(
        "--dcc-port",
        default=0,
        type=int,
        help=("DCC RPC server port. 0 means auto-assign (default: 0)"),
    )
    group.addoption(
        "--dcc-timeout",
        default=10.0,
        type=float,
        help="Default RPC call timeout in seconds (default: 10)",
    )
    group.addoption(
        "--dcc-startup-timeout",
        default=60.0,
        type=float,
        help=(
            "Seconds to wait for DCC to start and "
            "server to be ready (default: 60)"
        ),
    )
