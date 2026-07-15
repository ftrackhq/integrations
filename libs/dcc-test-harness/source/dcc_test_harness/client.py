"""External RPC client for communicating with a DCC's test server.

Runs outside the DCC in Python 3.13. Provides a Pythonic API
for test authors to interact with the DCC application.
"""

from __future__ import annotations

import socket
import threading
from typing import Any, Optional

from dcc_test_harness._protocol import (
    make_request,
    read_message,
    write_message,
)
from dcc_test_harness.exceptions import (
    DCCConnectionError,
    RPCError,
    RPCTimeoutError,
    WidgetNotFoundError,
)


class WidgetProxy:
    """Lightweight proxy for a Qt widget inside the DCC.

    Holds a widget_id and a reference to the DCCClient. All method
    calls translate to ``qt.widget_action`` RPC calls.
    """

    def __init__(self, client: DCCClient, info: dict) -> None:
        self._client = client
        self._info = info
        self._widget_id: int = info["widget_id"]

    @property
    def widget_id(self) -> int:
        return self._widget_id

    @property
    def object_name(self) -> str:
        return self._info.get("object_name", "")

    @property
    def widget_type(self) -> str:
        return self._info.get("widget_type", "")

    @property
    def text(self) -> Optional[str]:
        return self._info.get("text")

    @property
    def visible(self) -> Optional[bool]:
        return self._info.get("visible")

    @property
    def enabled(self) -> Optional[bool]:
        return self._info.get("enabled")

    def click(self) -> None:
        self._action("click")

    def double_click(self) -> None:
        self._action("double_click")

    def set_text(self, text: str) -> None:
        self._action("set_text", text=text)

    def set_value(self, value: Any) -> None:
        self._action("set_value", value=value)

    def set_combo_text(self, text: str) -> None:
        self._action("set_combo_text", text=text)

    def set_combo_index(self, index: int) -> None:
        self._action("set_combo_index", index=index)

    def set_checked(self, checked: bool) -> None:
        self._action("set_checked", checked=checked)

    def close(self) -> None:
        self._action("close")

    def children(self, **query: Any) -> list[WidgetProxy]:
        result = self._client.call(
            "qt.list_children",
            {"widget_id": self._widget_id, **query},
        )
        return [WidgetProxy(self._client, info) for info in result]

    def parent(self) -> Optional[WidgetProxy]:
        result = self._client.call(
            "qt.widget_action",
            {
                "widget_id": self._widget_id,
                "action": "get_parent",
                "args": {},
            },
        )
        if isinstance(result, dict) and "widget_id" in result:
            return WidgetProxy(self._client, result)
        return None

    def refresh(self) -> None:
        result = self._client.call(
            "qt.widget_action",
            {
                "widget_id": self._widget_id,
                "action": "refresh",
                "args": {},
            },
        )
        if isinstance(result, dict):
            self._info = result

    def _action(self, action: str, **kwargs: Any) -> Any:
        return self._client.call(
            "qt.widget_action",
            {
                "widget_id": self._widget_id,
                "action": action,
                "args": kwargs,
            },
        )

    def __repr__(self) -> str:
        return (
            f"<WidgetProxy {self.widget_type}"
            f" name={self.object_name!r}"
            f" text={self.text!r}>"
        )


class DCCClient:
    """RPC client for communicating with a DCC test server.

    Example::

        client = DCCClient(port=9876)
        client.connect()
        result = client.execute("__result__ = 1 + 1")
        client.disconnect()
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 9876,
        timeout: float = 10.0,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self._sock: Optional[socket.socket] = None
        self._request_id = 0
        self._lock = threading.Lock()

    def connect(self) -> None:
        """Establish a TCP connection to the DCC test server."""
        if self._sock is not None:
            return
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.host, self.port))
            self._sock = sock
        except OSError as e:
            raise DCCConnectionError(
                f"Cannot connect to DCC at {self.host}:{self.port}: {e}"
            ) from e

    def disconnect(self) -> None:
        """Close the TCP connection."""
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

    def ping(self) -> bool:
        """Check if the server is responsive."""
        try:
            result = self.call("ping")
            return result.get("status") == "ok"
        except Exception:
            return False

    def call(
        self,
        method: str,
        params: Optional[dict] = None,
        timeout: Optional[float] = None,
    ) -> Any:
        """Send a JSON-RPC request and return the result.

        Raises RPCError on server-side errors,
        RPCTimeoutError on timeout.
        """
        if self._sock is None:
            raise DCCConnectionError("Not connected")

        with self._lock:
            self._request_id += 1
            request_id = self._request_id

            request = make_request(method, params, request_id)

            effective_timeout = timeout or self.timeout
            self._sock.settimeout(effective_timeout)

            try:
                write_message(self._sock, request)
                response = read_message(self._sock)
            except socket.timeout as e:
                raise RPCTimeoutError(
                    f"RPC call {method!r} timed out after {effective_timeout}s"
                ) from e
            except (ConnectionError, OSError) as e:
                self._sock = None
                raise DCCConnectionError(
                    f"Connection lost during {method!r}: {e}"
                ) from e

        if response is None:
            self._sock = None
            raise DCCConnectionError("Connection closed by server")

        if "error" in response:
            error = response["error"]
            code = error.get("code", -32000)
            message = error.get("message", "Unknown error")
            data = error.get("data", {})
            remote_tb = data.get("traceback")

            if code == -32002:
                raise WidgetNotFoundError(params or {})

            raise RPCError(
                code=code,
                message=message,
                remote_traceback=remote_tb,
            )

        return response.get("result")

    def execute(self, code: str) -> Any:
        """Execute arbitrary Python code inside the DCC.

        Set ``__result__`` in the code to return a value::

            client.execute('''
            __result__ = some_function()
            ''')
        """
        return self.call("exec", {"code": code})

    def evaluate(self, expression: str) -> Any:
        """Evaluate a Python expression inside the DCC."""
        return self.call("eval", {"expression": expression})

    def find_widget(self, **query: Any) -> Optional[WidgetProxy]:
        """Find a single widget matching the query.

        Returns None if no match.
        """
        result = self.call("qt.find_widget", query)
        if result is None:
            return None
        return WidgetProxy(self, result)

    def find_widgets(self, **query: Any) -> list[WidgetProxy]:
        """Find all widgets matching the query."""
        results = self.call("qt.find_widgets", query)
        return [WidgetProxy(self, info) for info in results]

    def wait_for_widget(
        self, timeout: float = 5.0, **query: Any
    ) -> WidgetProxy:
        """Wait for a widget to appear, polling with timeout.

        Raises WidgetNotFoundError if not found within timeout.
        """
        query["timeout"] = timeout
        result = self.call("qt.wait_for_widget", query, timeout=timeout + 5.0)
        if result is None:
            raise WidgetNotFoundError(query)
        return WidgetProxy(self, result)

    def shutdown_server(self) -> None:
        """Ask the DCC-side server to shut down."""
        try:
            self.call("shutdown", timeout=5.0)
        except (DCCConnectionError, RPCTimeoutError):
            pass

    def __repr__(self) -> str:
        status = "connected" if self._sock is not None else "disconnected"
        return f"<DCCClient {self.host}:{self.port} ({status})>"
