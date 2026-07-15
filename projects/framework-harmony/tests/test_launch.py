# :coding: utf-8
# :copyright: Copyright (c) 2026 ftrack

"""Tier-1 launch tests: Harmony starts through the Connect launch
path and the ftrack JS package bootstraps.

No ftrack server or credentials required - the test process plays
the standalone framework process' role over the TCP wire protocol.
"""

import re

UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-" r"[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def test_harmony_process_alive(harmony_process):
    """Harmony launched via the Connect launch config and stays up."""
    assert harmony_process.is_alive(), (
        "Harmony exited prematurely.\n"
        f"--- Harmony output tail ---\n"
        f"{harmony_process.log_tail()}"
    )


def test_js_package_handshake(harmony_connection):
    """The context-data handshake is acknowledged.

    A reply proves the whole JS bootstrap chain: the package was
    deployed and loaded (configure.js ran), the TCP server is up,
    session-id filtering matches, and the ftrack menu was built -
    configure.js only replies after ``handleIntegrationContextDataCallback``
    created the menu entries.
    """
    reply = harmony_connection.handshake_reply
    assert reply is not None
    assert (
        reply["data"]["integration_session_id"]
        == harmony_connection.session_id
    )


def test_rpc_utils_included(harmony_connection):
    """RPC round-trip against a function defined in utils.js.

    Proves the package-relative ``include()`` calls in configure.js
    resolved.
    """
    result = harmony_connection.rpc("uuidv4")["result"]
    assert UUID_PATTERN.match(result), result


def test_rpc_reaches_harmony_api(harmony_connection):
    """RPC evaluation reaches Harmony's scripting API."""
    result = harmony_connection.rpc("about.productName")["result"]
    assert "harmony" in str(result).lower(), result


def test_rpc_error_reported(harmony_connection):
    """Unknown functions surface an error message, not a hang."""
    data = harmony_connection.rpc(
        "ftrackThisFunctionDoesNotExist", expect_error=True
    )
    assert data.get("error_message")
