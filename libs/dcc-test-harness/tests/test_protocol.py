"""Unit tests for the RPC protocol and client.

These tests run without a DCC application, using a mock
TCP server to verify the protocol round-trip.
"""

import socket
import threading

from dcc_test_harness._protocol import (
    decode_message,
    encode_message,
    make_error,
    make_request,
    make_response,
    read_message,
    write_message,
)
from dcc_test_harness.client import DCCClient
from dcc_test_harness.exceptions import (
    DCCConnectionError,
    RPCError,
)


class TestMessageEncoding:
    """Test message encoding and decoding."""

    def test_encode_decode_roundtrip(self):
        msg = {"jsonrpc": "2.0", "id": 1, "method": "ping"}
        encoded = encode_message(msg)
        # First 4 bytes are the length header
        assert len(encoded) > 4
        payload = encoded[4:]
        decoded = decode_message(payload)
        assert decoded == msg

    def test_encode_unicode(self):
        msg = {"text": "hello \u00e9\u00e8\u00ea"}
        encoded = encode_message(msg)
        payload = encoded[4:]
        decoded = decode_message(payload)
        assert decoded["text"] == "hello \u00e9\u00e8\u00ea"

    def test_encode_nested(self):
        msg = {"data": {"list": [1, 2, 3], "nested": {"a": True}}}
        encoded = encode_message(msg)
        payload = encoded[4:]
        decoded = decode_message(payload)
        assert decoded == msg


class TestMessageBuilders:
    """Test JSON-RPC message construction."""

    def test_make_request(self):
        req = make_request("ping", None, 1)
        assert req["jsonrpc"] == "2.0"
        assert req["id"] == 1
        assert req["method"] == "ping"
        assert "params" not in req

    def test_make_request_with_params(self):
        req = make_request("exec", {"code": "1+1"}, 42)
        assert req["params"] == {"code": "1+1"}
        assert req["id"] == 42

    def test_make_response(self):
        resp = make_response(1, {"status": "ok"})
        assert resp["jsonrpc"] == "2.0"
        assert resp["id"] == 1
        assert resp["result"] == {"status": "ok"}

    def test_make_error(self):
        err = make_error(1, -32000, "fail", {"traceback": "..."})
        assert err["error"]["code"] == -32000
        assert err["error"]["message"] == "fail"
        assert err["error"]["data"]["traceback"] == "..."

    def test_make_error_no_data(self):
        err = make_error(1, -32601, "not found")
        assert "data" not in err["error"]


class _MockServer:
    """Minimal TCP server for testing the client."""

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(1)
        self.sock.settimeout(5)
        self.port = self.sock.getsockname()[1]
        self._handlers = []
        self._thread = None

    def expect(self, handler):
        """Register a handler: callable(request) -> response dict."""
        self._handlers.append(handler)
        return self

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def _run(self):
        conn, _ = self.sock.accept()
        try:
            for handler in self._handlers:
                msg = read_message(conn)
                if msg is None:
                    break
                response = handler(msg)
                if response is not None:
                    write_message(conn, response)
        finally:
            conn.close()
            self.sock.close()

    def join(self):
        if self._thread:
            self._thread.join(timeout=5)


class TestClientRoundTrip:
    """Test DCCClient against a mock server."""

    def test_ping(self):
        server = _MockServer()
        server.expect(
            lambda req: make_response(req["id"], {"status": "ok"})
        ).start()

        client = DCCClient(port=server.port, timeout=5.0)
        client.connect()
        assert client.ping() is True
        client.disconnect()
        server.join()

    def test_execute(self):
        server = _MockServer()
        server.expect(lambda req: make_response(req["id"], 42)).start()

        client = DCCClient(port=server.port, timeout=5.0)
        client.connect()
        result = client.execute("__result__ = 42")
        assert result == 42
        client.disconnect()
        server.join()

    def test_evaluate(self):
        server = _MockServer()
        server.expect(
            lambda req: make_response(req["id"], "hello world")
        ).start()

        client = DCCClient(port=server.port, timeout=5.0)
        client.connect()
        result = client.evaluate("'hello ' + 'world'")
        assert result == "hello world"
        client.disconnect()
        server.join()

    def test_rpc_error(self):
        server = _MockServer()
        server.expect(
            lambda req: make_error(req["id"], -32000, "something broke")
        ).start()

        client = DCCClient(port=server.port, timeout=5.0)
        client.connect()
        try:
            client.call("bad_method")
            assert False, "Should have raised RPCError"
        except RPCError as e:
            assert e.code == -32000
            assert "something broke" in str(e)
        client.disconnect()
        server.join()

    def test_connection_error_when_not_connected(self):
        client = DCCClient(port=99999, timeout=1.0)
        try:
            client.call("ping")
            assert False, "Should have raised DCCConnectionError"
        except DCCConnectionError:
            pass

    def test_shutdown_server(self):
        server = _MockServer()
        server.expect(
            lambda req: make_response(req["id"], {"status": "shutting_down"})
        ).start()

        client = DCCClient(port=server.port, timeout=5.0)
        client.connect()
        client.shutdown_server()  # should not raise
        client.disconnect()
        server.join()

    def test_multiple_calls(self):
        call_count = {"n": 0}

        def handler(req):
            call_count["n"] += 1
            return make_response(req["id"], call_count["n"])

        server = _MockServer()
        server.expect(handler).expect(handler).expect(handler).start()

        client = DCCClient(port=server.port, timeout=5.0)
        client.connect()
        assert client.call("a") == 1
        assert client.call("b") == 2
        assert client.call("c") == 3
        client.disconnect()
        server.join()


class TestSocketReadWrite:
    """Test read_message / write_message over real sockets."""

    def test_roundtrip_over_socket(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("127.0.0.1", 0))
        srv.listen(1)
        srv.settimeout(5)
        port = srv.getsockname()[1]

        sent_msg = {
            "jsonrpc": "2.0",
            "id": 99,
            "result": [1, 2, 3],
        }

        def server_fn():
            conn, _ = srv.accept()
            write_message(conn, sent_msg)
            conn.close()
            srv.close()

        t = threading.Thread(target=server_fn, daemon=True)
        t.start()

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(5)
        client.connect(("127.0.0.1", port))
        received = read_message(client)
        client.close()
        t.join()

        assert received == sent_msg

    def test_read_returns_none_on_closed(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("127.0.0.1", 0))
        srv.listen(1)
        srv.settimeout(5)
        port = srv.getsockname()[1]

        def server_fn():
            conn, _ = srv.accept()
            conn.close()
            srv.close()

        t = threading.Thread(target=server_fn, daemon=True)
        t.start()

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(5)
        client.connect(("127.0.0.1", port))
        result = read_message(client)
        client.close()
        t.join()

        assert result is None
