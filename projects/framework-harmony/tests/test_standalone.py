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
them. This module covers the exact bootstrap chain that previously
crashed on Python 3.13 in ``registry.scan_extensions``.
"""

import re

import pytest

from dcc_test_harness.connect_launcher import resolve_ftrack_credentials

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


def test_client_bootstrapped(standalone_bundle):
    """Host/Client and the ftrack session came up."""
    result = standalone_bundle.client.execute(
        "import ftrack_framework_harmony as fh\n"
        "__result__ = fh.client_instance is not None"
    )
    assert result is True


def test_registry_scanned(standalone_bundle):
    """Extensions were scanned (previously crashed on Python 3.13 in
    ``registry.scan_extensions``), including the new opener/snapshot
    extensions."""
    result = standalone_bundle.client.execute(
        "import ftrack_framework_harmony as fh\n"
        "registry = fh.client_instance.registry\n"
        "__result__ = {\n"
        "    'tool_configs': sorted(\n"
        "        item['name'] for item in (registry.tool_configs or [])\n"
        "    ),\n"
        "    'plugins': sorted(\n"
        "        item['name'] for item in (registry.plugins or [])\n"
        "    ),\n"
        "}"
    )
    assert "harmony-image-sequence-publisher" in result["tool_configs"]
    assert "harmony-scene-opener" in result["tool_configs"]
    assert "harmony_sequence_exporter" in result["plugins"]
    assert "harmony_scene_exporter" in result["plugins"]
    assert "harmony_scene_opener" in result["plugins"]


def test_tcp_link_to_harmony(standalone_bundle):
    """The standalone process holds a live TCP link to Harmony."""
    result = standalone_bundle.client.execute(
        "from ftrack_framework_harmony.utils import TCPRPCClient\n"
        "__result__ = TCPRPCClient._instance.connected"
    )
    assert result is True


def test_full_chain_rpc(standalone_bundle):
    """pytest -> standalone process -> Harmony JS eval -> back."""
    result = standalone_bundle.client.execute(
        "from ftrack_framework_harmony.utils import TCPRPCClient\n"
        "__result__ = TCPRPCClient.instance().rpc(\n"
        "    'uuidv4', timeout=60000\n"
        ")['result']"
    )
    assert UUID_PATTERN.match(result), result


def test_process_survives_dialog_close(standalone_bundle):
    """The standalone process must outlive individual dialogs.

    ``QApplication.quitOnLastWindowClosed`` must be False - otherwise
    closing the publisher dialog quits the process, dropping the TCP
    link to Harmony, and the ftrack menu only opens a dialog once.
    """
    result = standalone_bundle.client.execute(
        "try:\n"
        "    from PySide6 import QtWidgets\n"
        "except ImportError:\n"
        "    from PySide2 import QtWidgets\n"
        "__result__ = "
        "QtWidgets.QApplication.instance().quitOnLastWindowClosed()"
    )
    assert result is False


def test_save_scene_rpc(standalone_bundle):
    """The saveScene JS command (used by the snapshot exporter) works."""
    result = standalone_bundle.client.execute(
        "from ftrack_framework_harmony.utils import TCPRPCClient\n"
        "__result__ = TCPRPCClient.instance().rpc(\n"
        "    'saveScene', timeout=120000\n"
        ")['result']"
    )
    assert result is True


def test_scene_path_rpc(standalone_bundle):
    """getScenePath returns the current scene folder on disk."""
    result = standalone_bundle.client.execute(
        "import os\n"
        "from ftrack_framework_harmony.utils import TCPRPCClient\n"
        "path = TCPRPCClient.instance().rpc("
        "'getScenePath', timeout=30000)['result']\n"
        "__result__ = {'path': path, 'exists': os.path.isdir(path)}"
    )
    assert result["path"]
    assert result["exists"] is True


def test_open_scene_round_trip(standalone_bundle):
    """Snapshot + opener round trip at the RPC level (no ftrack server).

    Saves the scene, locates its .xstage on disk, and re-opens it via
    ``openScene`` (``scene.closeSceneAndOpenOffline``). Runs last as it
    closes and reopens the current scene.
    """
    result = standalone_bundle.client.execute(
        "import os\n"
        "from ftrack_framework_harmony.utils import TCPRPCClient\n"
        "conn = TCPRPCClient.instance()\n"
        "conn.rpc('saveScene', timeout=120000)\n"
        "folder = conn.rpc('getScenePath', timeout=30000)['result']\n"
        "xstage = None\n"
        "for root, _dirs, files in os.walk(folder):\n"
        "    for fn in files:\n"
        "        if fn.endswith('.xstage'):\n"
        "            xstage = os.path.join(root, fn)\n"
        "            break\n"
        "    if xstage:\n"
        "        break\n"
        "opened = None\n"
        "if xstage:\n"
        "    opened = conn.rpc(\n"
        "        'openScene', [xstage.replace(chr(92), '/')],"
        " timeout=120000\n"
        "    ).get('result')\n"
        "__result__ = {'xstage': xstage, 'opened': opened}"
    )
    assert result["xstage"], "No .xstage found in the current scene folder"
    assert result["opened"] is True
