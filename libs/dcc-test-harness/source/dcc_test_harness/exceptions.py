"""Exception hierarchy for the DCC test harness.

Shared by both the external client and the DCC-side server.
Must remain compatible with Python 3.11+.
"""

from __future__ import annotations

from typing import Optional


class DCCTestHarnessError(Exception):
    """Base exception for all dcc-test-harness errors."""


class DCCConnectionError(DCCTestHarnessError):
    """Raised when the TCP connection cannot be established or is lost."""


class RPCError(DCCTestHarnessError):
    """Raised when a DCC-side RPC call returns an error."""

    def __init__(
        self,
        code: int,
        message: str,
        remote_traceback: Optional[str] = None,
    ):
        self.code = code
        self.remote_traceback = remote_traceback
        super().__init__(f"[{code}] {message}")


class RPCTimeoutError(DCCTestHarnessError):
    """Raised when an RPC call or connection attempt exceeds the timeout."""


class WidgetNotFoundError(DCCTestHarnessError):
    """Raised when a Qt widget query returns no matches."""

    def __init__(self, query: dict):
        self.query = query
        super().__init__(f"No widget found matching: {query}")
