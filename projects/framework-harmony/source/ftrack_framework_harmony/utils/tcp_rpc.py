# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import logging
import json
import time
import uuid
import os
import sys

try:
    from PySide6 import QtWidgets, QtCore, QtNetwork
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtNetwork

import ftrack_constants.framework as constants
from ftrack_utils.framework.remote import get_remote_integration_session_id


class TCPRPCClient(QtCore.QObject):
    '''TCP client facilitating communication with DCC:s not able
    to import or use any ftrack API (Javascript)'''

    MAX_WRITE_RESPONSE_TIME = 10000
    INT32_SIZE = 4
    REPLY_WAIT_TIMEOUT = 5 * 60 * 1000  # Wait 5 minutes tops

    # Connection should be a singleton accessible also during plugin execution
    _instance = None

    @property
    def dcc_name(self):
        '''Return DCC name.'''
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
        '''Return DCC version.'''
        return self._dcc_version

    @property
    def remote_integration_session_id(self):
        return self._remote_integration_session_id

    @property
    def process_events_callback(self):
        '''Return callback for processing events.'''
        return self._process_events_callback

    @property
    def on_connected_callback(self):
        '''Return callback for connection establish.'''
        return self._on_connected_callback

    @property
    def on_run_tool_callback(self):
        '''Return callback for run dialog event.'''
        return self._on_run_tool_callback

    @property
    def connected(self):
        '''Return True if connected to DCC.'''
        return self._connected

    @connected.setter
    def connected(self, value):
        '''Set connected state to *value*.'''
        self._connected = value
        if self._connected:
            self.logger.info(
                f'Successfully established connection to {self.dcc_name} '
                f'v{self.dcc_version} @ {self.address}:{self.port}'
            )

    @property
    def connection_status(self):
        '''Return the connection status of the socket'''
        return self.socket.state()

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
        '''
        Initialise the TCP RPC client

        :param dcc_name: The name of the DCC; 'harmony', etc.
        :param address: The hostname or IP to connect to
        :param port: The port to connect to
        :param client: Framework client
        :param launchers: The launchers to send be created in the DCC menus
        :param on_connected_callback: The callback to run when DCC is connected
        :param on_run_tool_callback: The callback to run when a tool is requested to run
        :param process_events_callback: The callback to run when holding up the main thread
        :param parent:
        '''

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

        self._failure_callback = None
        self._connection_attempts = None
        self._handle_reply_event_callback = None
        self._blocksize = 0
        self._reply_event_data = None

        self._initialise()

    @staticmethod
    def instance():
        '''Return the singleton instance, checks if it is initialised and connected.'''
        assert TCPRPCClient._instance, 'TCP RPC instance not created!'
        assert (
            TCPRPCClient._instance.connected
        ), 'DCC not connected, please keep panel open while integration is working!'

        return TCPRPCClient._instance

    def _initialise(self):
        '''Initialise the TCP client, create socket.'''
        env_name = f'FTRACK_{self.dcc_name.upper()}_VERSION'
        self._dcc_version = os.environ.get(env_name)
        assert self.dcc_version, (
            f'{self.dcc_name.title()} integration requires {env_name} passed as'
            f' environment variable!'
        )

        self._remote_integration_session_id = (
            get_remote_integration_session_id()
        )
        assert self.remote_integration_session_id, (
            f'{self.dcc_name.title()} integration requires FTRACK_REMOTE_INTEGRATION_SESSION_ID'
            ' passed as environment variable!'
        )

        self.socket = QtNetwork.QTcpSocket(self)
        self.socket.connected.connect(self._on_connected)
        self._buffer = None
        self._receiving = False
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self._check_connection)

        self.logger = logging.getLogger(__name__)

        self.logger.info('Initialized TCP client')

    def _check_connection(self):
        '''Check connection status and try to reconnect if necessary.'''
        end_time = time.time()
        elapsed = end_time - self._start_time
        self.logger.debug(f'Connection status: {self.connection_status}')
        if (
            self.connection_status
            == QtNetwork.QAbstractSocket.SocketState.ConnectedState
        ):
            result = self.connection_status
            self.logger.debug(
                f'Connect took ({self._start_time - end_time} s), status: {result}'
            )

            self.connected = True

            # Send launchers for DCC to create menus, expect reply back as an
            # acknowledgment that DCC is ready
            self.send(
                constants.event.REMOTE_INTEGRATION_CONTEXT_DATA_TOPIC,
                {
                    'context_id': self.client.context_id,
                    'launchers': self._launchers,
                },
                synchronous=True,
            )

            self._timer.stop()
            self.on_connected_callback()
        elif (
            self.connection_status
            != QtNetwork.QAbstractSocket.SocketState.ConnectingState
        ):
            # Connection refused, DCC not up yet
            self._connection_attempts -= 1
            if self._connection_attempts == 0:
                self.logger.error(f'DCC never launched, giving up.')
                self._failure_callback()
            else:
                self.logger.warning('DCC not up yet, reconnecting in 2s')
                self._timer.stop()
                time.sleep(2)
                self._connect_to_host()
        else:
            if elapsed > 60:
                self.logger.error(
                    f'Error connecting to the DCC event hub (waited: {elapsed}s)'
                    f' Details: {self.socket.error()}'
                )
                self._failure_callback()
            else:
                self.logger.warning(
                    f'Could not connect to the DCC event hub (waited: {elapsed}s), '
                    f'retrying. Details: {self.socket.error()}'
                )

    def connect_dcc(self, failure_callback):
        '''Connect to the DCC event hub.'''
        if self.connected:
            self.logger.warning(
                f'Connection already existed , removing connection to {self.address} {self.port} '
            )
            self.socket.abort()

        self._failure_callback = failure_callback
        self._connection_attempts = 60  # Wait 2mins for DCC to start

        self.logger.info(
            f'Connecting to DCC event hub @ {self.address}:{self.port} '
        )

        self._connect_to_host()

    def _connect_to_host(self):
        self._start_time = time.time()
        self.socket.connectToHost(self.address, self.port)
        self._timer.start(1000)

    def _on_bytes_written(self, bytes):
        '''Callback on *bytes* written to the socket'''
        self.logger.debug(f'Connection bytes written: {bytes}')

    def _on_state_changed(self, state):
        '''Callback on *state* change of the socket'''
        self.logger.debug(f'Connect state changed: {state}')

    def _on_ready_read(self):
        '''Callback on ready read from the socket'''
        if not self._receiving:
            self._receive()

    def _on_connected(self):
        '''Callback on successful connection to the socket'''
        self.logger.info('Setting up connection options...')
        self.socket.setSocketOption(
            QtNetwork.QTcpSocket.SocketOption.LowDelayOption, 1
        )
        self.socket.setSocketOption(
            QtNetwork.QTcpSocket.SocketOption.KeepAliveOption, 1
        )

        self.socket.readyRead.connect(self._on_ready_read)
        self.socket.bytesWritten.connect(self._on_bytes_written)
        self.socket.stateChanged.connect(self._on_state_changed)
        self.socket.disconnected.connect(self._on_disconnected)

    def _send(self, data):
        '''Send *data* to the DCC as string.'''
        # make sure we are connected
        if self.socket.state() in (
            QtNetwork.QAbstractSocket.SocketState.UnconnectedState,
        ):
            raise Exception('Not connected to Harmony')

        block = QtCore.QByteArray()

        outstr = QtCore.QDataStream(
            block, QtCore.QIODevice.OpenModeFlag.WriteOnly
        )
        outstr.setVersion(QtCore.QDataStream.Version.Qt_4_6)

        outstr.writeString(str(data))

        self.socket.write(block)

        if not self.socket.waitForBytesWritten(self.MAX_WRITE_RESPONSE_TIME):
            self.logger.error(
                f'Could not write to socket: {self.socket.errorString()}'
            )
        else:
            self.logger.debug(f'Sent data ok. {self.socket.state()}')

    def _receive(self):
        '''Receive data from the DCC'''
        self.logger.debug('Receiving data')

        stream = QtCore.QDataStream(self.socket)
        stream.setVersion(QtCore.QDataStream.Version.Qt_4_6)

        i = 0
        while self.socket.bytesAvailable() > 0:
            if (
                self._blocksize == 0
                and self.socket.bytesAvailable() >= self.INT32_SIZE
            ) or (0 < self._blocksize <= self.socket.bytesAvailable()):
                self._blocksize = stream.readInt32()
            if 0 < self._blocksize <= self.socket.bytesAvailable():
                data = stream.readRawData(self._blocksize)
                raw_event = data.decode('utf-8')
                self._decode_and_process_event(raw_event)
                self._blocksize = 0
                i += 1

        return None

    def _decode_and_process_event(self, raw_event):
        '''Load and process incoming *raw_event* from the DCC.'''
        self.logger.info(f'Decoding incoming event: {str(raw_event)}')
        try:
            event = json.loads(raw_event)
        except Exception as e:
            self.logger.warning(
                f'Ignoring request, not well formed! Details: {e}'
            )
            return None

        # Is this event for us?
        event_data = event.get('data')
        if not event_data:
            self.logger.warning(f'Ignoring request, no data. {raw_event}')
            return None

        session_id = event_data.get('integration_session_id')

        if session_id != self.remote_integration_session_id:
            self.logger.warning(f'Ignoring event, not for us. {raw_event}')
            return None

        # Is someone waiting for a reply?
        if self._handle_reply_event_callback:
            if event.get('in_reply_to_event') == self._reply_id:
                self.logger.info(f'Got reply for event: {self._reply_id}')
                self._handle_reply_event_callback(
                    event['topic'], event_data, event['id']
                )
                return None

        if (
            event['topic']
            == constants.event.REMOTE_INTEGRATION_RUN_DIALOG_TOPIC
        ):
            self.on_run_tool_callback(
                event['data']['name'],
                event['data']['dialog_name'],
                event['data']['options'],
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
        '''
        Send an event to the DCC

        @param topic: The topic of the event
        @param event_data: The data of the event
        @param in_reply_to_event: The event to reply to
        @param synchronous: If the event should be sent synchronously
        @param timeout: The timeout in seconds to wait for a response, -1 and it will wait forever.
        '''
        event_data[
            'remote_integration_session_id'
        ] = self.remote_integration_session_id
        event = {
            'id': str(uuid.uuid4()),
            'topic': topic,
            'data': event_data,
        }
        if in_reply_to_event:
            event['in_reply_to_event'] = in_reply_to_event

        st = time.time()
        self._send(json.dumps(event))
        et = time.time()
        self.logger.info(
            f'Sent {topic} event (took: {(et - st)} secs): {event}'
        )

        if synchronous:
            self._reply_event_data = None

            def handle_reply_event(topic, event_data, id):
                self.logger.info(
                    f'Registering incoming reply event: {topic} ({id}), '
                    f'data: {event_data}'
                )
                self._reply_event_data = event_data

            self._reply_id = event['id']
            self._handle_reply_event_callback = handle_reply_event

            wait = timeout or self.REPLY_WAIT_TIMEOUT
            waited = 0
            try:
                self.logger.info(
                    f'Waiting to receive reply for {event["id"]}...'
                )
                while True:
                    if self.process_events_callback:
                        self.process_events_callback()
                    time.sleep(0.1)
                    waited += 100

                    if -1 < wait <= waited:
                        raise Exception(
                            f'Timeout waiting for reply for event: {event["id"]}'
                        )
                    elif waited % 2000 == 0:
                        self.logger.info(
                            f'Waited {int(waited / 1000)}s for reply...'
                        )

                    if self._reply_event_data:
                        return self._reply_event_data

            finally:
                self._handle_reply_event_callback = None
                self._reply_id = None

    def send_reply(self, event, data):
        '''Send a reply to an event back to DCC'''
        self.send(event['topic'], data, in_reply_to_event=event['id'])

    def rpc(self, function_name, args=None, timeout=None):
        '''
        Make a remote procedure call to the DCC and return the result.

        :param function_name: The function to execute
        :param args: The arguments to pass
        :param timeout: The timeout in seconds to wait for a response, -1 and it will wait forever.
        :return: The result return from DCC.
        '''

        data = {
            'remote_integration_session_id': self.remote_integration_session_id,
            'function_name': function_name,
            'args': args or [],
        }

        self.logger.debug(f'Running {self.dcc_name.title()} RPC call: {data}')

        event_topic = constants.event.REMOTE_INTEGRATION_RPC_TOPIC

        response = self.send(event_topic, data, None, True, timeout=timeout)

        self.logger.debug(
            f'Got {self.dcc_name.title()} RPC response: {response}'
        )

        if not isinstance(response, dict):
            raise Exception(
                f'Internal error, response is not an dictionary: {response}'
            )

        return response

    def error(self, socketError):
        '''Handle socket errors'''
        if (
            socketError
            == QtNetwork.QAbstractSocket.SocketError.RemoteHostClosedError
        ):
            self.logger.error('Host closed the connection.')
        elif (
            socketError
            == QtNetwork.QAbstractSocket.SocketError.HostNotFoundError
        ):
            self.logger.error(
                'The host was not found. Please check the address and ' 'port.'
            )
        elif (
            socketError
            == QtNetwork.QAbstractSocket.SocketError.ConnectionRefusedError
        ):
            self.logger.error('The server is not up and running yet.')
        else:
            self.logger.error(
                f'The following error occurred: {self.socket.errorString()}.'
            )

    def close(self):
        '''Close the connection to the DCC.'''
        self.socket.abort()

    def _on_disconnected(self):
        '''Callback on disconnection from the socket'''
        self.logger.warning(
            f'Connection to Harmony lost, gracefully terminating integration'
        )
        sys.exit(0)
