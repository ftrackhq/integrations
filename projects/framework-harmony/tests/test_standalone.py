# :coding: utf-8
# :copyright: Copyright (c) 2026 ftrack

"""Tier-2 tests: the full production stack.

Harmony is launched through the Connect launch path and the real
standalone framework process is spawned next to it, exactly like
Connect does. The dcc-test-harness server is injected into the
standalone process so the tests can assert on the live integration:
ftrack session, Host/Client, extension registry and the TCP link to
Harmony.

Requires ftrack credentials (``FTRACK_SERVER``/``FTRACK_API_KEY``
env vars, or a previous ftrack Connect login) - skipped without
them. This module covers the exact bootstrap chain that failed with
the pre-#641 builds (``registry.scan_extensions`` on Python 3.13).
"""

import os
import platform
import re
import ssl
import tempfile
import time
from pathlib import Path

import pytest

from dcc_test_harness.client import DCCClient
from dcc_test_harness.connect_launcher import (
    resolve_ftrack_credentials,
)
from dcc_test_harness.exceptions import DCCConnectionError

UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-" r"[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

pytestmark = pytest.mark.skipif(
    resolve_ftrack_credentials() is None,
    reason=(
        "ftrack credentials required: set FTRACK_SERVER and "
        "FTRACK_API_KEY, or log in via ftrack Connect"
    ),
)


def _tail(log_path, lines=40):
    try:
        with open(log_path, "r", errors="replace") as f:
            return "".join(f.readlines()[-lines:])
    except OSError:
        return "<no output captured>"


@pytest.fixture(scope="module")
def standalone_client(request, harmony_launcher, harmony_process):
    """The standalone framework process, inspectable via the harness.

    Spawned with the same environment as Harmony (as Connect does)
    plus the ftrack credentials Connect would inject.
    """
    credentials = resolve_ftrack_credentials()
    port_file = tempfile.mktemp(prefix="harmony_standalone_", suffix=".port")

    extra_env = {
        "FTRACK_SERVER": credentials["server"],
        "FTRACK_API_KEY": credentials["api_key"],
        "FTRACK_APIKEY": credentials["api_key"],
        "FTRACK_EVENT_SERVER": credentials["server"],
        "DCC_TEST_PORT_FILE": port_file,
    }
    if credentials["api_user"]:
        extra_env["FTRACK_API_USER"] = credentials["api_user"]
    # DCC/bundled Pythons often ship outdated CA certs; Connect's
    # environment provides working ones for the event hub.
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
    try:
        port = harmony_launcher._wait_for_port_file(
            port_file,
            request.config.getoption("dcc_startup_timeout"),
            process,
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

        # Wait until the integration has connected to Harmony, so
        # the tests observe a fully bootstrapped state.
        deadline = time.monotonic() + request.config.getoption(
            "dcc_startup_timeout"
        )
        while True:
            connected = client.execute(
                "from ftrack_framework_harmony.utils import"
                " TCPRPCClient\n"
                "__result__ = ("
                "TCPRPCClient._instance is not None"
                " and TCPRPCClient._instance.connected)"
            )
            if connected:
                break
            if time.monotonic() > deadline:
                pytest.fail(
                    "Standalone process never connected to "
                    "Harmony.\n"
                    f"--- standalone output tail ---\n"
                    f"{_tail(log_path)}\n"
                    f"--- Harmony windows ---\n"
                    f"{harmony_process.describe_windows()}"
                )
            time.sleep(1.0)
    except BaseException:
        # BaseException so pytest.fail()/KeyboardInterrupt also
        # clean up the spawned process.
        if client is not None:
            client.disconnect()
        process.kill()
        process.wait(timeout=10)
        raise
    finally:
        try:
            os.unlink(port_file)
        except OSError:
            pass

    yield client

    # Clean shutdown: quit the Qt loop via the harness, then make
    # sure the process is gone.
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


def test_client_bootstrapped(standalone_client):
    """Host/Client and the ftrack session came up."""
    result = standalone_client.execute(
        "import ftrack_framework_harmony as fh\n"
        "__result__ = fh.client_instance is not None"
    )
    assert result is True


def test_registry_scanned(standalone_client):
    """Extensions were scanned (the pre-#641 py3.13 crash site)."""
    result = standalone_client.execute(
        "import ftrack_framework_harmony as fh\n"
        "registry = fh.client_instance.registry\n"
        "__result__ = {\n"
        "    'tool_configs': sorted(\n"
        "        item['name']\n"
        "        for item in (registry.tool_configs or [])\n"
        "    ),\n"
        "    'plugins': sorted(\n"
        "        item['name']\n"
        "        for item in (registry.plugins or [])\n"
        "    ),\n"
        "}"
    )
    assert "harmony-image-sequence-publisher" in result["tool_configs"]
    assert "harmony_sequence_exporter" in result["plugins"]


def test_tcp_link_to_harmony(standalone_client):
    """The standalone process holds a live TCP link to Harmony."""
    result = standalone_client.execute(
        "from ftrack_framework_harmony.utils import TCPRPCClient\n"
        "__result__ = TCPRPCClient._instance.connected"
    )
    assert result is True


def test_full_chain_rpc(standalone_client):
    """pytest -> standalone process -> Harmony JS eval -> back."""
    result = standalone_client.execute(
        "from ftrack_framework_harmony.utils import TCPRPCClient\n"
        "__result__ = TCPRPCClient.instance().rpc(\n"
        "    'uuidv4', timeout=60000\n"
        ")['result']"
    )
    assert UUID_PATTERN.match(result), result


def test_process_survives_dialog_close(standalone_client):
    """The standalone process must outlive individual dialogs.

    ``QApplication.quitOnLastWindowClosed`` must be False - otherwise
    closing the publisher dialog quits the process, dropping the TCP
    link to Harmony, and the ftrack menu only opens a dialog once.
    """
    result = standalone_client.execute(
        "try:\n"
        "    from PySide6 import QtWidgets\n"
        "except ImportError:\n"
        "    from PySide2 import QtWidgets\n"
        "__result__ = "
        "QtWidgets.QApplication.instance().quitOnLastWindowClosed()"
    )
    assert result is False
