"""DCC-side RPC server.

Runs inside a DCC's Python interpreter. Receives JSON-RPC requests
over TCP, dispatches them on the main thread via QTimer, and returns
results.

DCC-agnostic: no Maya/Nuke/Houdini imports. DCC-specific commands
are executed through the generic ``exec`` and ``eval`` methods.
Must remain compatible with Python 3.11+.
"""

from __future__ import annotations

import logging
import queue
import socket
import threading
import traceback
from typing import Any, Callable, Optional

from dcc_test_harness._protocol import (
    make_error,
    make_response,
    read_message,
    write_message,
)

logger = logging.getLogger(__name__)

# Error codes (JSON-RPC 2.0 server error range: -32000 to -32099)
ERR_INTERNAL = -32000
ERR_METHOD_NOT_FOUND = -32601
ERR_INVALID_PARAMS = -32602
ERR_TIMEOUT = -32001
ERR_WIDGET_NOT_FOUND = -32002
ERR_WIDGET_INVALID = -32003

# Global server instance for management
_server_instance: Optional[TestServer] = None


class _CommandResult:
    """Holds the result of a command executed on the main thread."""

    __slots__ = ("event", "result", "error")

    def __init__(self) -> None:
        self.event = threading.Event()
        self.result: Any = None
        self.error: Optional[dict] = None


class _WidgetRegistry:
    """Tracks Qt widgets by id() to prevent GC and enable cross-call refs."""

    def __init__(self) -> None:
        self._widgets: dict[int, Any] = {}

    def register(self, widget: Any) -> int:
        wid = id(widget)
        self._widgets[wid] = widget
        return wid

    def get(self, widget_id: int) -> Any:
        widget = self._widgets.get(widget_id)
        if widget is None:
            return None
        try:
            import shiboken6

            if not shiboken6.isValid(widget):
                del self._widgets[widget_id]
                return None
        except ImportError:
            pass
        return widget

    def clear(self) -> None:
        self._widgets.clear()


class CommandDispatcher:
    """Dispatches RPC method calls to the appropriate handler."""

    def __init__(self) -> None:
        self.widget_registry = _WidgetRegistry()

    def dispatch(self, method: str, params: Optional[dict]) -> Any:
        if params is None:
            params = {}

        if method == "ping":
            return {"status": "ok"}

        if method == "exec":
            return self._dispatch_exec(params)

        if method == "eval":
            return self._dispatch_eval(params)

        if method.startswith("qt."):
            return self._dispatch_qt(method, params)

        raise _MethodNotFoundError(method)

    def _dispatch_exec(self, params: dict) -> Any:
        code = params.get("code", "")
        local_ns: dict[str, Any] = {}
        exec(code, {"__builtins__": __builtins__}, local_ns)
        result = local_ns.get("__result__")
        return _make_serializable(result)

    def _dispatch_eval(self, params: dict) -> Any:
        expression = params.get("expression", "")
        result = eval(expression)
        return _make_serializable(result)

    def _dispatch_qt(self, method: str, params: dict) -> Any:
        if method == "qt.find_widget":
            return self._qt_find_widget(params)
        if method == "qt.find_widgets":
            return self._qt_find_widgets(params)
        if method == "qt.widget_action":
            return self._qt_widget_action(params)
        if method == "qt.list_children":
            return self._qt_list_children(params)
        if method == "qt.wait_for_widget":
            return self._qt_wait_for_widget(params)
        raise _MethodNotFoundError(method)

    def _qt_find_widget(self, params: dict) -> Optional[dict]:
        widgets = self._qt_search(params)
        if not widgets:
            return None
        index = params.get("index", 0)
        if index >= len(widgets):
            return None
        return self._serialize_widget(widgets[index])

    def _qt_find_widgets(self, params: dict) -> list[dict]:
        widgets = self._qt_search(params)
        return [self._serialize_widget(w) for w in widgets]

    def _qt_widget_action(self, params: dict) -> Any:
        widget_id = params.get("widget_id")
        action = params.get("action", "")
        action_args = params.get("args", {})

        widget = self.widget_registry.get(widget_id)
        if widget is None:
            raise _WidgetInvalidError(widget_id)

        return self._perform_widget_action(widget, action, action_args)

    def _qt_list_children(self, params: dict) -> list[dict]:
        widget_id = params.get("widget_id")
        widget = self.widget_registry.get(widget_id)
        if widget is None:
            raise _WidgetInvalidError(widget_id)

        query = {k: v for k, v in params.items() if k != "widget_id"}
        children = self._search_children(widget, query)
        return [self._serialize_widget(c) for c in children]

    def _qt_wait_for_widget(self, params: dict) -> Optional[dict]:
        import time

        timeout = params.get("timeout", 5.0)
        poll_interval = params.get("poll_interval", 0.1)
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            widgets = self._qt_search(params)
            if widgets:
                index = params.get("index", 0)
                if index < len(widgets):
                    return self._serialize_widget(widgets[index])
            time.sleep(poll_interval)

        return None

    def _qt_search(self, params: dict) -> list:
        from PySide6.QtWidgets import QApplication

        candidates: list = []

        window_title = params.get("window_title")
        top_level = QApplication.topLevelWidgets()

        if window_title:
            top_level = [
                w
                for w in top_level
                if hasattr(w, "windowTitle")
                and w.windowTitle() == window_title
            ]

        for tlw in top_level:
            candidates.extend(self._collect_all_widgets(tlw))

        return self._filter_widgets(candidates, params)

    def _collect_all_widgets(self, root: Any) -> list:
        result = [root]
        for child in root.children():
            from PySide6.QtWidgets import QWidget

            if isinstance(child, QWidget):
                result.extend(self._collect_all_widgets(child))
        return result

    def _search_children(self, parent: Any, query: dict) -> list:
        children = []
        for child in parent.children():
            from PySide6.QtWidgets import QWidget

            if isinstance(child, QWidget):
                children.extend(self._collect_all_widgets(child))
        return self._filter_widgets(children, query)

    def _filter_widgets(self, widgets: list, params: dict) -> list:
        result = widgets

        object_name = params.get("object_name")
        if object_name is not None:
            result = [w for w in result if w.objectName() == object_name]

        widget_type = params.get("widget_type")
        if widget_type is not None:
            result = [w for w in result if type(w).__name__ == widget_type]

        text = params.get("text")
        if text is not None:
            result = [w for w in result if self._get_widget_text(w) == text]

        visible_only = params.get("visible_only", True)
        if visible_only:
            result = [
                w for w in result if hasattr(w, "isVisible") and w.isVisible()
            ]

        return result

    def _get_widget_text(self, widget: Any) -> Optional[str]:
        for attr in ("text", "windowTitle", "title", "currentText"):
            getter = getattr(widget, attr, None)
            if getter is not None and callable(getter):
                try:
                    return getter()
                except Exception:
                    pass
        return None

    def _serialize_widget(self, widget: Any) -> dict:
        widget_id = self.widget_registry.register(widget)
        return {
            "widget_id": widget_id,
            "object_name": widget.objectName(),
            "widget_type": type(widget).__name__,
            "text": self._get_widget_text(widget),
            "visible": (
                widget.isVisible() if hasattr(widget, "isVisible") else None
            ),
            "enabled": (
                widget.isEnabled() if hasattr(widget, "isEnabled") else None
            ),
        }

    def _perform_widget_action(
        self, widget: Any, action: str, args: dict
    ) -> Any:
        from PySide6 import QtCore, QtWidgets

        if action == "click":
            if isinstance(widget, QtWidgets.QAbstractButton):
                widget.click()
            elif isinstance(widget, QtWidgets.QAction):
                widget.trigger()
            else:
                from PySide6.QtCore import QEvent, QPoint
                from PySide6.QtGui import QMouseEvent

                center = widget.rect().center()
                press = QMouseEvent(
                    QEvent.Type.MouseButtonPress,
                    QPoint(center.x(), center.y()),
                    QtCore.Qt.MouseButton.LeftButton,
                    QtCore.Qt.MouseButton.LeftButton,
                    QtCore.Qt.KeyboardModifier.NoModifier,
                )
                release = QMouseEvent(
                    QEvent.Type.MouseButtonRelease,
                    QPoint(center.x(), center.y()),
                    QtCore.Qt.MouseButton.LeftButton,
                    QtCore.Qt.MouseButton.LeftButton,
                    QtCore.Qt.KeyboardModifier.NoModifier,
                )
                QtWidgets.QApplication.postEvent(widget, press)
                QtWidgets.QApplication.postEvent(widget, release)
            return None

        if action == "double_click":
            from PySide6.QtCore import QEvent, QPoint
            from PySide6.QtGui import QMouseEvent

            center = widget.rect().center()
            dbl = QMouseEvent(
                QEvent.Type.MouseButtonDblClick,
                QPoint(center.x(), center.y()),
                QtCore.Qt.MouseButton.LeftButton,
                QtCore.Qt.MouseButton.LeftButton,
                QtCore.Qt.KeyboardModifier.NoModifier,
            )
            QtWidgets.QApplication.postEvent(widget, dbl)
            return None

        if action == "set_text":
            text = args.get("text", "")
            if isinstance(widget, QtWidgets.QLineEdit):
                widget.setText(text)
            elif isinstance(widget, QtWidgets.QTextEdit):
                widget.setPlainText(text)
            else:
                widget.setText(text)
            return None

        if action == "set_value":
            value = args.get("value")
            if hasattr(widget, "setValue"):
                widget.setValue(value)
            return None

        if action == "set_combo_text":
            text = args.get("text", "")
            if isinstance(widget, QtWidgets.QComboBox):
                idx = widget.findText(text)
                if idx >= 0:
                    widget.setCurrentIndex(idx)
            return None

        if action == "set_combo_index":
            index = args.get("index", 0)
            if isinstance(widget, QtWidgets.QComboBox):
                widget.setCurrentIndex(index)
            return None

        if action == "set_checked":
            checked = args.get("checked", False)
            if hasattr(widget, "setChecked"):
                widget.setChecked(checked)
            return None

        if action == "close":
            widget.close()
            return None

        if action == "get_parent":
            parent = widget.parent()
            if parent is None:
                return None
            return self._serialize_widget(parent)

        if action == "get_property":
            prop = args.get("property", "")
            return _make_serializable(getattr(widget, prop, None))

        if action == "refresh":
            return self._serialize_widget(widget)

        raise ValueError(f"Unknown widget action: {action}")


class TestServer:
    """TCP server that receives RPC requests and dispatches them on
    the DCC's main thread via QTimer."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 0,
        port_file: Optional[str] = None,
        quit_fn: Optional[Callable[[], None]] = None,
    ) -> None:
        self.host = host
        self.port = port
        self.port_file = port_file
        self._quit_fn = quit_fn
        self.dispatcher = CommandDispatcher()
        self._command_queue: queue.Queue = queue.Queue()
        self._server_socket: Optional[socket.socket] = None
        self._server_thread: Optional[threading.Thread] = None
        self._timer: Optional[Any] = None
        self._running = False
        self._quit_requested = False

    def start(self) -> int:
        """Start the server. Returns the actual bound port."""
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
        )
        self._server_socket.bind((self.host, self.port))
        self._server_socket.listen(1)
        self._server_socket.settimeout(1.0)

        actual_port = self._server_socket.getsockname()[1]
        self.port = actual_port

        if self.port_file:
            with open(self.port_file, "w") as f:
                f.write(str(actual_port))

        self._running = True

        self._server_thread = threading.Thread(
            target=self._accept_loop,
            daemon=True,
            name="dcc-test-server",
        )
        self._server_thread.start()

        self._start_timer()

        logger.info(
            "DCC test server listening on %s:%d",
            self.host,
            actual_port,
        )
        print(f"DCC_TEST_SERVER_PORT={actual_port}")

        return actual_port

    def stop(self) -> None:
        """Stop the server and clean up."""
        self._running = False

        if self._timer is not None:
            self._timer.stop()
            self._timer = None

        if self._server_socket is not None:
            try:
                self._server_socket.close()
            except OSError:
                pass
            self._server_socket = None

        if self._server_thread is not None:
            self._server_thread.join(timeout=5.0)
            self._server_thread = None

        self.dispatcher.widget_registry.clear()
        logger.info("DCC test server stopped")

    def _initiate_shutdown(self) -> None:
        """Signal a graceful shutdown from the background thread.

        Sets a flag that the QTimer callback (main thread) checks.
        The actual quit happens on the main thread at a safe point
        in the Qt event loop, avoiding SIGTERM-during-paint crashes.
        """
        self._quit_requested = True
        self._running = False

        if self._server_socket is not None:
            try:
                self._server_socket.close()
            except OSError:
                pass

    def _start_timer(self) -> None:
        from PySide6.QtCore import QTimer

        self._timer = QTimer()
        self._timer.setInterval(10)
        self._timer.timeout.connect(self._process_commands)
        self._timer.start()

    def _process_commands(self) -> None:
        """Process pending commands on the main thread (called by QTimer)."""
        if self._quit_requested:
            self._timer.stop()
            self._timer = None
            self.dispatcher.widget_registry.clear()
            if self._quit_fn is not None:
                try:
                    self._quit_fn()
                except Exception:
                    pass
            return

        while not self._command_queue.empty():
            try:
                request_id, method, params, cmd_result = (
                    self._command_queue.get_nowait()
                )
            except queue.Empty:
                break

            try:
                result = self.dispatcher.dispatch(method, params)
                cmd_result.result = make_response(request_id, result)
            except _MethodNotFoundError as e:
                cmd_result.error = make_error(
                    request_id,
                    ERR_METHOD_NOT_FOUND,
                    str(e),
                )
            except _WidgetInvalidError as e:
                cmd_result.error = make_error(
                    request_id,
                    ERR_WIDGET_INVALID,
                    str(e),
                )
            except Exception:
                tb = traceback.format_exc()
                cmd_result.error = make_error(
                    request_id,
                    ERR_INTERNAL,
                    traceback.format_exception_only(
                        *__import__("sys").exc_info()[:2]
                    )[-1].strip(),
                    data={"traceback": tb},
                )
            finally:
                cmd_result.event.set()

    def _accept_loop(self) -> None:
        """Background thread: accept connections and handle requests."""
        while self._running:
            try:
                client_sock, addr = self._server_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            logger.info("Client connected from %s", addr)
            try:
                self._handle_client(client_sock)
            except Exception:
                logger.exception("Error handling client")
            finally:
                try:
                    client_sock.close()
                except OSError:
                    pass
                logger.info("Client disconnected")

    def _handle_client(self, client_sock: socket.socket) -> None:
        """Handle a single client connection."""
        while self._running:
            try:
                msg = read_message(client_sock)
            except (ConnectionError, OSError):
                break
            if msg is None:
                break

            request_id = msg.get("id", 0)
            method = msg.get("method", "")
            params = msg.get("params")

            if method == "ping":
                write_message(
                    client_sock,
                    make_response(request_id, {"status": "ok"}),
                )
                continue

            if method == "shutdown":
                write_message(
                    client_sock,
                    make_response(request_id, {"status": "shutting_down"}),
                )
                self._initiate_shutdown()
                return

            cmd_result = _CommandResult()
            self._command_queue.put((request_id, method, params, cmd_result))

            if not cmd_result.event.wait(timeout=30.0):
                write_message(
                    client_sock,
                    make_error(
                        request_id,
                        ERR_TIMEOUT,
                        "Command timed out waiting for main thread",
                    ),
                )
                continue

            response = cmd_result.result or cmd_result.error
            if response:
                try:
                    write_message(client_sock, response)
                except (ConnectionError, OSError):
                    break


class _MethodNotFoundError(Exception):
    def __init__(self, method: str) -> None:
        super().__init__(f"Method not found: {method}")


class _WidgetInvalidError(Exception):
    def __init__(self, widget_id: Any) -> None:
        super().__init__(
            f"Widget {widget_id} is no longer valid "
            f"(destroyed or garbage collected)"
        )


def _make_serializable(obj: Any) -> Any:
    """Coerce a value to something JSON-serializable."""
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, (list, tuple)):
        return [_make_serializable(item) for item in obj]
    if isinstance(obj, dict):
        return {str(k): _make_serializable(v) for k, v in obj.items()}
    return str(obj)


def start(
    host: str = "127.0.0.1",
    port: int = 0,
    port_file: Optional[str] = None,
    quit_fn: Optional[Callable[[], None]] = None,
) -> TestServer:
    """Start the test server inside a DCC application.

    Args:
        host: Bind address.
        port: Port to listen on. 0 means OS picks a free port.
        port_file: If set, write the actual port to this file path.
        quit_fn: Optional callback to quit the DCC on shutdown.
            Called on the main thread. Example for Maya:
            ``lambda: maya.cmds.quit(force=True)``

    Returns:
        The running TestServer instance.
    """
    global _server_instance

    if _server_instance is not None:
        logger.warning("Stopping existing server instance")
        _server_instance.stop()

    server = TestServer(
        host=host, port=port, port_file=port_file, quit_fn=quit_fn
    )
    server.start()
    _server_instance = server
    return server


def stop() -> None:
    """Stop the running test server."""
    global _server_instance
    if _server_instance is not None:
        _server_instance.stop()
        _server_instance = None
