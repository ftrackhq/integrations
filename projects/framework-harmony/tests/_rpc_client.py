# :coding: utf-8
# :copyright: Copyright (c) 2026 ftrack

"""Minimal TCP client speaking the Harmony integration wire protocol.

The ftrack JS package inside Harmony (resource/bootstrap/js/configure.js)
runs a TCP server which the standalone framework process connects to.
This client implements the same protocol using only the standard
library, so tier-1 tests can play the standalone process' role and
verify Harmony launched and bootstrapped the integration correctly.

Wire framing (asymmetric, see also
source/ftrack_framework_harmony/utils/tcp_rpc.py):

- client -> Harmony: big-endian ``uint32(len + 1)`` + UTF-8 JSON +
  trailing NUL byte (``QDataStream.writeString`` semantics - the JS
  read loop strips the NUL).
- Harmony -> client: big-endian ``int32(len)`` + raw UTF-8 JSON.

Every event carries the remote integration session id -
``remote_integration_session_id`` in events sent to Harmony,
``integration_session_id`` in events received from Harmony. Replies
reference the originating event through ``in_reply_to_event``.
"""

from __future__ import annotations

import json
import logging
import socket
import struct
import time
import uuid
from typing import Optional

logger = logging.getLogger(__name__)

# Wire protocol topics, mirrored in configure.js and
# ftrack_constants.framework.event.
_BASE = "ftrack.framework"
REMOTE_INTEGRATION_CONTEXT_DATA_TOPIC = (
    _BASE + ".remote.integration.context.data"
)
REMOTE_INTEGRATION_RUN_DIALOG_TOPIC = _BASE + ".remote.integration.run.dialog"
REMOTE_INTEGRATION_RPC_TOPIC = _BASE + ".remote.integration.rpc"

#: Launcher payloads matching the tools in extensions/harmony.yaml,
#: sent with the context-data handshake so Harmony builds the real menu.
PUBLISH_LAUNCHER = {
    "name": "publish",
    "label": "Publish",
    "dialog_name": "framework_standard_publisher_dialog",
    "options": {
        "tool_configs": ["harmony-image-sequence-publisher"],
        "docked": False,
    },
}
OPEN_LAUNCHER = {
    "name": "open",
    "label": "Open",
    "dialog_name": "framework_standard_opener_dialog",
    "options": {
        "tool_configs": ["harmony-scene-opener"],
        "docked": False,
    },
}
# Mirrors the tool order in extensions/harmony.yaml (menu/toolbar order).
DEFAULT_LAUNCHERS = [OPEN_LAUNCHER, PUBLISH_LAUNCHER]


class HarmonyRPCError(RuntimeError):
    """An RPC call was answered with an error by Harmony."""


class HarmonyRPCTestClient:
    """Test double for the standalone framework process' TCP client."""

    def __init__(
        self,
        host: str,
        port: int,
        session_id: str,
        timeout: float = 30.0,
    ) -> None:
        self.host = host
        self.port = port
        self.session_id = session_id
        self.timeout = timeout
        self.handshake_reply: Optional[dict] = None
        self._sock: Optional[socket.socket] = None

    # -- Connection --

    def connect_with_retry(
        self, is_alive=None, timeout: float = 120.0
    ) -> None:
        """Connect to the JS TCP server inside Harmony.

        Retries until *timeout*, failing fast if *is_alive* (an
        optional no-arg callable) reports the DCC has died.
        """
        deadline = time.monotonic() + timeout
        last_error: Optional[Exception] = None
        while time.monotonic() < deadline:
            if is_alive is not None and not is_alive():
                raise RuntimeError(
                    "Harmony exited before the ftrack JS TCP server came up."
                )
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            try:
                sock.connect((self.host, self.port))
            except OSError as error:
                last_error = error
                sock.close()
                time.sleep(0.5)
                continue
            sock.settimeout(self.timeout)
            self._sock = sock
            logger.info(
                "Connected to Harmony JS server @ %s:%s",
                self.host,
                self.port,
            )
            return
        raise TimeoutError(
            f"Could not connect to Harmony JS TCP server at "
            f"{self.host}:{self.port} within {timeout}s - the "
            f"ftrack package probably did not load. "
            f"Last error: {last_error}"
        )

    def close(self) -> None:
        if self._sock is not None:
            try:
                self._sock.close()
            finally:
                self._sock = None

    # -- Framing --

    def send_event(
        self,
        topic: str,
        data: dict,
        in_reply_to: Optional[str] = None,
    ) -> str:
        """Send an event to Harmony, returning the event id."""
        assert self._sock is not None, "Not connected"
        payload_data = dict(data)
        payload_data["remote_integration_session_id"] = self.session_id
        event = {
            "id": str(uuid.uuid4()),
            "topic": topic,
            "data": payload_data,
        }
        if in_reply_to:
            event["in_reply_to_event"] = in_reply_to
        payload = json.dumps(event).encode("utf-8")
        # QDataStream.writeString framing: length includes the
        # terminating NUL.
        frame = struct.pack(">I", len(payload) + 1) + payload + b"\x00"
        self._sock.sendall(frame)
        logger.debug("Sent event: %s", event)
        return event["id"]

    def _recv_exact(self, size: int, deadline: float) -> bytes:
        assert self._sock is not None, "Not connected"
        buffer = b""
        while len(buffer) < size:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Timed out reading from Harmony")
            self._sock.settimeout(remaining)
            chunk = self._sock.recv(size - len(buffer))
            if not chunk:
                raise ConnectionError("Harmony closed the connection")
            buffer += chunk
        return buffer

    def read_event(self, deadline: float) -> dict:
        """Read one length-prefixed JSON event from Harmony."""
        header = self._recv_exact(4, deadline)
        (size,) = struct.unpack(">i", header)
        payload = self._recv_exact(size, deadline)
        event = json.loads(payload.decode("utf-8"))
        logger.debug("Received event: %s", event)
        return event

    # -- Protocol --

    def wait_for_reply(self, event_id: str, timeout: float = 60.0) -> dict:
        """Wait for the reply to *event_id*.

        Events for other sessions or unrelated topics are ignored,
        mirroring the standalone process' filtering.
        """
        deadline = time.monotonic() + timeout
        while True:
            event = self.read_event(deadline)
            data = event.get("data") or {}
            if data.get("integration_session_id") != self.session_id:
                logger.warning("Ignoring event for other session: %s", event)
                continue
            if event.get("in_reply_to_event") == event_id:
                return event

    def handshake(
        self,
        launchers: Optional[list] = None,
        timeout: float = 60.0,
    ) -> dict:
        """Send the context-data event and await the acknowledgment.

        Harmony only replies after it has built the ftrack menu from
        *launchers*, so a reply proves the JS package bootstrapped.
        """
        event_id = self.send_event(
            REMOTE_INTEGRATION_CONTEXT_DATA_TOPIC,
            {
                "context_id": None,
                "launchers": (
                    launchers if launchers is not None else DEFAULT_LAUNCHERS
                ),
            },
        )
        self.handshake_reply = self.wait_for_reply(event_id, timeout)
        return self.handshake_reply

    def rpc(
        self,
        function_name: str,
        args: Optional[list] = None,
        timeout: float = 60.0,
        expect_error: bool = False,
    ) -> dict:
        """Call a JS function inside Harmony and return the reply data."""
        event_id = self.send_event(
            REMOTE_INTEGRATION_RPC_TOPIC,
            {
                "function_name": function_name,
                "args": args or [],
            },
        )
        reply = self.wait_for_reply(event_id, timeout)
        data = reply.get("data") or {}
        if data.get("error_message") and not expect_error:
            raise HarmonyRPCError(data["error_message"])
        return data
