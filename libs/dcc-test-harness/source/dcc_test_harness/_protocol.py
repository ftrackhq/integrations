"""JSON-RPC 2.0 protocol over TCP with length-prefixed framing.

Shared by both the external client and the DCC-side server.
Must remain compatible with Python 3.11+.
"""

from __future__ import annotations

import json
import socket
import struct
from typing import Any, Optional

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 0  # OS-assigned
HEADER_SIZE = 4  # bytes, big-endian uint32 length prefix
JSONRPC_VERSION = "2.0"


def encode_message(obj: dict) -> bytes:
    """Encode a dict as a length-prefixed JSON message."""
    payload = json.dumps(obj, default=_json_default).encode("utf-8")
    header = struct.pack("!I", len(payload))
    return header + payload


def decode_message(data: bytes) -> dict:
    """Decode a JSON payload (without the length header)."""
    return json.loads(data.decode("utf-8"))


def read_message(sock: socket.socket) -> Optional[dict]:
    """Read one length-prefixed JSON message from a socket.

    Returns None if the connection is closed.
    """
    header = _recv_exact(sock, HEADER_SIZE)
    if header is None:
        return None
    (length,) = struct.unpack("!I", header)
    payload = _recv_exact(sock, length)
    if payload is None:
        return None
    return decode_message(payload)


def write_message(sock: socket.socket, obj: dict) -> None:
    """Write one length-prefixed JSON message to a socket."""
    sock.sendall(encode_message(obj))


def make_request(
    method: str,
    params: Optional[dict] = None,
    request_id: int = 0,
) -> dict:
    """Build a JSON-RPC 2.0 request."""
    msg: dict[str, Any] = {
        "jsonrpc": JSONRPC_VERSION,
        "id": request_id,
        "method": method,
    }
    if params is not None:
        msg["params"] = params
    return msg


def make_response(request_id: int, result: Any) -> dict:
    """Build a JSON-RPC 2.0 success response."""
    return {
        "jsonrpc": JSONRPC_VERSION,
        "id": request_id,
        "result": result,
    }


def make_error(
    request_id: int,
    code: int,
    message: str,
    data: Optional[dict] = None,
) -> dict:
    """Build a JSON-RPC 2.0 error response."""
    error: dict[str, Any] = {
        "code": code,
        "message": message,
    }
    if data is not None:
        error["data"] = data
    return {
        "jsonrpc": JSONRPC_VERSION,
        "id": request_id,
        "error": error,
    }


def _recv_exact(sock: socket.socket, num_bytes: int) -> Optional[bytes]:
    """Read exactly num_bytes from a socket, or return None on EOF."""
    chunks: list[bytes] = []
    remaining = num_bytes
    while remaining > 0:
        chunk = sock.recv(min(remaining, 4096))
        if not chunk:
            return None
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _json_default(obj: object) -> Any:
    """Fallback serializer for non-standard types."""
    return str(obj)
