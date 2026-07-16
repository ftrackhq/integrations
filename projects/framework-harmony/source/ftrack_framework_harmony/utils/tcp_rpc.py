# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import logging
import json
import time
import uuid
import os

try:
    from PySide6 import QtCore, QtNetwork
except ImportError:
    from PySide2 import QtCore, QtNetwork

import ftrack_constants.framework as constants
from ftrack_utils.framework.remote import get_remote_integration_session_id


class TCPRPCClient(QtCore.QObject):
    """Role-agnostic RPC channel to a DCC that cannot import the ftrack
    API (Harmony/Javascript).

    This standalone process is the TCP *server*: it binds the port and
    keeps listening for Harmony's whole lifetime. Harmony is the client
    that dials out - at first launch and again after every scene
    open/create/close, because it tears down its Qt Script engine (and
    the dialed-out socket) on each scene switch. An external server
    outlives every scene switch, so the RPC channel never dies with the
    engine. The class name is kept (callers do
    ``TCPRPCClient.instance().rpc(...)``); only the socket lifecycle
    moved from dialing out to listening.
    """

    MAX_WRITE_RESPONSE_TIME = 10000
    INT32_SIZE = 4
    REPLY_WAIT_TIMEOUT = 5 * 60 * 1000  # Wait 5 minutes tops

    # Connection should be a singleton accessible also during plugin execution
    _instance = None

    @property
    def dcc_name(self):
        """Return DCC name."""
        return self._dcc_name

    @property
    def address(self):
        return self._address

    @property
    def port(self):
        return self._port

    @property
    def client(self):
        return self._client

    @property
    def dcc_version(self):
        """Return DCC version."""
        return self._dcc_version

    @property
    def remote_integration_session_id(self):
        return self._remote_integration_session_id

    @property
    def process_events_callback(self):
        """Return callback for processing events."""
        return self._process_events_callback

    @property
    def on_connected_callback(self):
        """Return callback for connection establish."""
        return self._on_connected_callback

    @property
    def on_run_tool_callback(self):
        """Return callback for run dialog event."""
        return self._on_run_tool_callback

    @property
    def connected(self):
        """Return True if connected to DCC."""
        return self._connected

    @connected.setter
    def connected(self, value):
        """Set connected state to *value*."""
        self._connected = value
        if self._connected:
            self.logger.info(
                f"Successfully established connection to {self.dcc_name} "
                f"v{self.dcc_version} @ {self.address}:{self.port}"
            )

    @property
    def connection_status(self):
        """Return the state of the current DCC connection socket."""
        if self._connection is None:
            return QtNetwork.QAbstractSocket.SocketState.UnconnectedState
        return self._connection.state()

    def __init__(
        self,
        dcc_name,
        address,
        port,
        client,
        launchers,
        on_connected_callback,
        on_run_tool_callback,
        process_events_callback,
        parent=None,
    ):
        """
        Initialise the TCP RPC channel

        :param dcc_name: The name of the DCC; 'harmony', etc.
        :param address: The hostname or IP to bind (loopback)
        :param port: The port to listen on (Harmony dials this)
        :param client: Framework client
        :param launchers: The launchers to send be created in the DCC menus
        :param on_connected_callback: The callback to run when DCC is connected
        :param on_run_tool_callback: The callback to run when a tool is requested to run
        :param process_events_callback: The callback to run when holding up the main thread
        :param parent:
        """

        super(TCPRPCClient, self).__init__(parent=parent)

        # Store reference to self in class variable
        TCPRPCClient._instance = self

        self._dcc_name = dcc_name
        self._address = address
        self._port = port
        self._client = client
        self._launchers = launchers
        self._on_connected_callback = on_connected_callback
        self._on_run_tool_callback = on_run_tool_callback
        self._process_events_callback = process_events_callback
        self._connected = False
        # Startup tools must run only on the first connection, never on a
        # reconnect after a scene switch.
        self._ever_connected = False

        self._on_listen_failure = None
        self._handle_reply_event_callback = None
        self._blocksize = 0
        self._reply_event_data = None

        self._initialise()

    @staticmethod
    def instance():
        """Return the singleton instance, checks if it is initialised and connected."""
        assert TCPRPCClient._instance, "TCP RPC instance not created!"
        assert TCPRPCClient._instance.connected, "DCC not connected, please keep panel open while integration is working!"

        return TCPRPCClient._instance

    def _initialise(self):
        """Initialise the TCP RPC server."""
        env_name = f"FTRACK_{self.dcc_name.upper()}_VERSION"
        self._dcc_version = os.environ.get(env_name)
        assert self.dcc_version, (
            f"{self.dcc_name.title()} integration requires {env_name} passed as"
            f" environment variable!"
        )

        self._remote_integration_session_id = (
            get_remote_integration_session_id()
        )
        assert self.remote_integration_session_id, (
            f"{self.dcc_name.title()} integration requires FTRACK_REMOTE_INTEGRATION_SESSION_ID"
            " passed as environment variable!"
        )

        # This process is the TCP server; Harmony dials in. The server
        # outlives Harmony's Qt Script engine, so it survives every scene
        # switch (see class docstring).
        self._server = QtNetwork.QTcpServer(self)
        self._connection = None
        self._buffer = None
        self._receiving = False

        self.logger = logging.getLogger(__name__)

        self.logger.info("Initialized TCP RPC server")

    def listen(self, on_listen_failure):
        """Start the RPC server and await the DCC connection.

        Binds loopback (127.0.0.1) only: macOS does not raise a firewall
        prompt for loopback binds (never bind 0.0.0.0/Any). The server
        keeps listening for Harmony's whole lifetime, so each new Qt
        Script engine that dials in after a scene switch is accepted in
        :meth:`_on_new_connection`.

        :param on_listen_failure: Called if the port cannot be bound
            (e.g. already in use); the standalone then exits.
        """
        self._on_listen_failure = on_listen_failure

        # Loopback bind is load-bearing - see method docstring.
        address = QtNetwork.QHostAddress("127.0.0.1")
        if not self._server.listen(address, self.port):
            self.logger.error(
                f"Could not listen on 127.0.0.1:{self.port}: "
                f"{self._server.errorString()}"
            )
            self._on_listen_failure()
            return

        self._server.newConnection.connect(self._on_new_connection)
        self.logger.info(
            f"RPC server listening on 127.0.0.1:{self.port}, awaiting "
            f"{self.dcc_name} connection."
        )

    def _on_new_connection(self):
        """Accept a DCC connection.

        Harmony dials out every time it (re-)includes configure.js: at
        first launch and after every scene open/create/close (it tears
        down the Qt Script engine, and the old socket, on each scene
        switch). The server keeps listening across all of them, so each
        new engine simply reconnects here.

        The CONTEXT_DATA handshake rebuilds the ftrack menu on every
        (re)connection - Harmony drops script-added menu items on a scene
        switch - but the startup tools run only on the very first accept.
        """
        connection = self._server.nextPendingConnection()
        if connection is None:
            return

        # A scene switch leaves the previous socket half-dead; abort it so
        # only the freshest connection is used.
        if self._connection is not None:
            self._connection.abort()

        self._connection = connection
        self._blocksize = 0

        self.logger.info("Setting up connection options...")
        self._connection.setSocketOption(
            QtNetwork.QTcpSocket.SocketOption.LowDelayOption, 1
        )
        self._connection.setSocketOption(
            QtNetwork.QTcpSocket.SocketOption.KeepAliveOption, 1
        )

        # A fresh socket each time - wire per-connection signals directly.
        # The old socket is discarded, so no de-dup guard is needed.
        self._connection.readyRead.connect(self._on_ready_read)
        self._connection.bytesWritten.connect(self._on_bytes_written)
        self._connection.stateChanged.connect(self._on_state_changed)
        self._connection.disconnected.connect(self._on_disconnected)
        self._connection.errorOccurred.connect(self.error)

        self.connected = True

        # Send launchers so the DCC (re)builds its menus; expect a reply
        # back as an acknowledgment that the DCC is ready. Guard the whole
        # handshake: if the DCC drops mid-handshake (a fast scene switch),
        # send() fails fast rather than spinning - the server keeps
        # listening for the next reconnect, so swallow it here (this is a
        # Qt slot).
        try:
            self.send(
                constants.event.REMOTE_INTEGRATION_CONTEXT_DATA_TOPIC,
                {
                    "context_id": self.client.context_id,
                    "launchers": self._launchers,
                },
                synchronous=True,
            )
        except Exception as error:
            self.logger.warning(
                f"Context-data handshake did not complete (DCC likely "
                f"dropped the connection): {error}. Awaiting reconnect."
            )
            return

        # Startup tools run only on the first connection - a reconnect
        # after a scene switch must not relaunch them.
        if not self._ever_connected:
            self._ever_connected = True
            self.on_connected_callback()

    def _on_bytes_written(self, bytes):
        """Callback on *bytes* written to the socket"""
        self.logger.debug(f"Connection bytes written: {bytes}")

    def _on_state_changed(self, state):
        """Callback on *state* change of the socket"""
        self.logger.debug(f"Connect state changed: {state}")

    def _on_ready_read(self):
        """Callback on ready read from the socket"""
        if self._connection is None:
            return
        if not self._receiving:
            self._receive()

    def _send(self, data):
        """Send *data* to the DCC as string."""
        # make sure we are connected
        if self._connection is None or self._connection.state() in (
            QtNetwork.QAbstractSocket.SocketState.UnconnectedState,
        ):
            raise Exception("Not connected to Harmony")

        block = QtCore.QByteArray()

        outstr = QtCore.QDataStream(
            block, QtCore.QIODevice.OpenModeFlag.WriteOnly
        )
        outstr.setVersion(QtCore.QDataStream.Version.Qt_4_6)

        outstr.writeString(str(data))

        self._connection.write(block)

        if not self._connection.waitForBytesWritten(
            self.MAX_WRITE_RESPONSE_TIME
        ):
            self.logger.error(
                f"Could not write to socket: {self._connection.errorString()}"
            )
        else:
            self.logger.debug(f"Sent data ok. {self._connection.state()}")

    def _receive(self):
        """Receive data from the DCC"""
        self.logger.debug("Receiving data")

        stream = QtCore.QDataStream(self._connection)
        stream.setVersion(QtCore.QDataStream.Version.Qt_4_6)

        i = 0
        while self._connection.bytesAvailable() > 0:
            if (
                self._blocksize == 0
                and self._connection.bytesAvailable() >= self.INT32_SIZE
            ) or (0 < self._blocksize <= self._connection.bytesAvailable()):
                self._blocksize = stream.readInt32()
            if 0 < self._blocksize <= self._connection.bytesAvailable():
                data = stream.readRawData(self._blocksize)
                raw_event = data.decode("utf-8")
                self._decode_and_process_event(raw_event)
                self._blocksize = 0
                i += 1

        return None

    def _decode_and_process_event(self, raw_event):
        """Load and process incoming *raw_event* from the DCC."""
        self.logger.info(f"Decoding incoming event: {str(raw_event)}")
        try:
            event = json.loads(raw_event)
        except Exception as e:
            self.logger.warning(
                f"Ignoring request, not well formed! Details: {e}"
            )
            return None

        # Is this event for us?
        event_data = event.get("data")
        if not event_data:
            self.logger.warning(f"Ignoring request, no data. {raw_event}")
            return None

        session_id = event_data.get("integration_session_id")

        if session_id != self.remote_integration_session_id:
            self.logger.warning(f"Ignoring event, not for us. {raw_event}")
            return None

        # Is someone waiting for a reply?
        if self._handle_reply_event_callback:
            if event.get("in_reply_to_event") == self._reply_id:
                self.logger.info(f"Got reply for event: {self._reply_id}")
                self._handle_reply_event_callback(
                    event["topic"], event_data, event["id"]
                )
                return None

        if (
            event["topic"]
            == constants.event.REMOTE_INTEGRATION_RUN_DIALOG_TOPIC
        ):
            # Guard the dialog-construction callback so any exception
            # surfaces in the log instead of vanishing inside the Qt
            # readyRead slot (PySide swallows exceptions raised in a slot).
            # Mirrors the guarded handshake in _on_new_connection. Still
            # reply afterwards so the DCC is not left waiting.
            try:
                self.on_run_tool_callback(
                    event["data"]["name"],
                    event["data"]["dialog_name"],
                    event["data"]["options"],
                )
            except Exception:
                self.logger.exception(
                    f"on_run_tool_callback failed for tool "
                    f"{event['data']['name']} (dialog: "
                    f"{event['data']['dialog_name']})"
                )
            self.send_reply(event, {})

    def send(
        self,
        topic,
        event_data,
        in_reply_to_event=None,
        synchronous=False,
        timeout=None,
    ):
        """
        Send an event to the DCC

        @param topic: The topic of the event
        @param event_data: The data of the event
        @param in_reply_to_event: The event to reply to
        @param synchronous: If the event should be sent synchronously
        @param timeout: The timeout in seconds to wait for a response, -1 and it will wait forever.
        """
        event_data["remote_integration_session_id"] = (
            self.remote_integration_session_id
        )
        event = {
            "id": str(uuid.uuid4()),
            "topic": topic,
            "data": event_data,
        }
        if in_reply_to_event:
            event["in_reply_to_event"] = in_reply_to_event

        st = time.time()
        self._send(json.dumps(event))
        et = time.time()
        self.logger.info(
            f"Sent {topic} event (took: {(et - st)} secs): {event}"
        )

        if synchronous:
            self._reply_event_data = None

            def handle_reply_event(topic, event_data, id):
                self.logger.info(
                    f"Registering incoming reply event: {topic} ({id}), "
                    f"data: {event_data}"
                )
                self._reply_event_data = event_data

            self._reply_id = event["id"]
            self._handle_reply_event_callback = handle_reply_event

            wait = timeout or self.REPLY_WAIT_TIMEOUT
            waited = 0
            try:
                self.logger.info(
                    f"Waiting to receive reply for {event['id']}..."
                )
                while True:
                    if self.process_events_callback:
                        self.process_events_callback()
                    time.sleep(0.1)
                    waited += 100

                    # Fail fast if the DCC connection drops mid-wait (e.g.
                    # a scene switch during a long renderSequence) instead
                    # of spinning to the full timeout.
                    if not self.connected:
                        raise Exception(
                            f"DCC connection dropped while waiting for "
                            f"reply for event: {event['id']}"
                        )

                    if -1 < wait <= waited:
                        raise Exception(
                            f"Timeout waiting for reply for event: {event['id']}"
                        )
                    elif waited % 2000 == 0:
                        self.logger.info(
                            f"Waited {int(waited / 1000)}s for reply..."
                        )

                    if self._reply_event_data:
                        return self._reply_event_data

            finally:
                self._handle_reply_event_callback = None
                self._reply_id = None

    def send_reply(self, event, data):
        """Send a reply to an event back to DCC"""
        self.send(event["topic"], data, in_reply_to_event=event["id"])

    def rpc(self, function_name, args=None, timeout=None):
        """
        Make a remote procedure call to the DCC and return the result.

        :param function_name: The function to execute
        :param args: The arguments to pass
        :param timeout: The timeout in seconds to wait for a response, -1 and it will wait forever.
        :return: The result return from DCC.
        """

        data = {
            "remote_integration_session_id": self.remote_integration_session_id,
            "function_name": function_name,
            "args": args or [],
        }

        self.logger.debug(f"Running {self.dcc_name.title()} RPC call: {data}")

        event_topic = constants.event.REMOTE_INTEGRATION_RPC_TOPIC

        response = self.send(event_topic, data, None, True, timeout=timeout)

        self.logger.debug(
            f"Got {self.dcc_name.title()} RPC response: {response}"
        )

        if not isinstance(response, dict):
            raise Exception(
                f"Internal error, response is not an dictionary: {response}"
            )

        return response

    def error(self, socketError):
        """Handle socket errors"""
        if (
            socketError
            == QtNetwork.QAbstractSocket.SocketError.RemoteHostClosedError
        ):
            self.logger.error("Host closed the connection.")
        elif (
            socketError
            == QtNetwork.QAbstractSocket.SocketError.HostNotFoundError
        ):
            self.logger.error(
                "The host was not found. Please check the address and port."
            )
        elif (
            socketError
            == QtNetwork.QAbstractSocket.SocketError.ConnectionRefusedError
        ):
            self.logger.error("The server is not up and running yet.")
        else:
            detail = (
                self._connection.errorString()
                if self._connection is not None
                else socketError
            )
            self.logger.error(f"The following error occurred: {detail}.")

    def close(self):
        """Stop listening and drop any live DCC connection."""
        self._server.close()
        if self._connection is not None:
            self._connection.abort()
            self._connection = None

    def _on_disconnected(self):
        """Callback on disconnection of the DCC socket.

        Harmony drops the TCP connection whenever it rebuilds its Qt
        Script engine on a scene open/create/close, even though the
        application keeps running. We simply reset state: the server
        keeps listening, and the next Qt Script engine reconnects via
        :meth:`_on_new_connection`, which re-sends the launcher context
        data so the JS side rebuilds the ftrack menu and toolbar.

        A genuine Harmony quit is handled solely by the process watchdog
        (process_watchdog_callback in __init__.py), which terminates this
        process once the Harmony PID is gone. This handler never
        terminates.
        """
        self.logger.warning(
            "DCC connection dropped (scene switch or quit); server still "
            "listening, awaiting reconnect. The process watchdog exits "
            "this process if Harmony has quit."
        )
        self.connected = False
        self._connection = None
        self._blocksize = 0
