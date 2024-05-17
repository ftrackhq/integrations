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
    def host(self):
        return self._host

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
    def on_run_dialog_callback(self):
        '''Return callback for run dialog event.'''
        return self._on_run_dialog_callback

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
                f'v{self.dcc_version} @ {self.host}:{self.port}'
            )

    def __init__(
        self,
        dcc_name,
        host,
        port,
        client,
        panel_launchers,
        on_run_dialog_callback,
        process_events_callback,
        parent=None,
    ):
        super(TCPRPCClient, self).__init__(parent=parent)

        # Store reference to self in class variable
        TCPRPCClient._instance = self

        self._dcc_name = dcc_name
        self._host = host
        self._port = port
        self._client = client
        self._panel_launchers = panel_launchers
        self._on_run_dialog_callback = on_run_dialog_callback
        self._process_events_callback = process_events_callback
        self._connected = False

        self._handle_reply_event_callback = None
        self._blocksize = 0
        self._callbacks = {}
        self.responses = {}
        self.awaiting_response = []

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

    def connection_status(self):
        return self.socket.state()

    def is_connected(self):
        return self.socket and (
            self.connection_status()
            == QtNetwork.QAbstractSocket.ConnectedState
        )

    def _check_connection(self):
        end_time = time.time()
        elapsed = end_time - self._start_time
        self.logger.debug(f'Connection status: {self.connection_status()}')
        if (
            self.connection_status()
            == QtNetwork.QAbstractSocket.ConnectedState
        ):
            result = self.connection_status()
            self.logger.debug(
                f'Connect took ({self._start_time - end_time} s), status: {result}'
            )

            self.connected = True

            # Send launchers for DCC to create menus, expect reply back as an
            # acknowledge that DCC is ready
            self.send(
                constants.event.REMOTE_INTEGRATION_CONTEXT_DATA_TOPIC,
                {
                    'context_id': self.client.context_id,
                    'panel_launchers': self._panel_launchers,
                },
                synchronous=True,
            )

            self._timer.stop()
            self._connected_callback()
        elif (
            self.connection_status()
            != QtNetwork.QAbstractSocket.ConnectingState
        ):
            # Connection refused, DCC not up yet
            self._connection_attempts -= 1
            if self._connection_attempts == 0:
                self.logger.error(f'DCC never launcher, giving up...')
                self._failure_callback()
            else:
                self.logger.warning('DCC not up yet, reconnecting in 2s')
                self._timer.stop()
                time.sleep(2)
                self._connect()
        else:
            if elapsed > 60:
                self.logger.error(
                    f'Error connecting to the DCC event hub (waited: {elapsed}s)'
                    f' Details: {self.socket.error()}'
                )
                self._failure_callback()
            else:
                self.logger.warning(
                    f'Could not connect to the DCC event hub (waited: {elapsed}s), retrying...'
                    f' Details: {self.socket.error()}'
                )

    def connect_dcc(self, connected_callback, failure_callback):
        if self.connected:
            self.logger.warning(
                f'Connection already existed , removing connection to {self.host} {self.port} '
            )
            self.socket.abort()

        self._connected_callback = connected_callback
        self._failure_callback = failure_callback
        self._connection_attempts = 30

        self.logger.info(
            f'Connecting to DCC event hub @ {self.host}:{self.port} '
        )

        self._connect()

    def _connect(self):
        self._start_time = time.time()
        self.socket.connectToHost(self.host, self.port)
        self._timer.start(1000)

    def _on_readyRead(self):
        self.logger.warning('Ready to read')

    def _on_error(self):
        self.logger.debug(f'Error occurred: {self.socket.errorString()}')

    def _on_bytes_written(self, bytes):
        self.logger.debug(f'Connection bytes written: {bytes}')

    def _on_state_changed(self, state):
        self.logger.debug(f'Connect state changed: {state}')

    def _on_connected(self):
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
        # make sure we are connected
        if self.socket.state() in (
            QtNetwork.QAbstractSocket.SocketState.UnconnectedState,
        ):
            self.connect()

        block = QtCore.QByteArray()

        outstr = QtCore.QDataStream(block, QtCore.QIODevice.WriteOnly)
        outstr.setVersion(QtCore.QDataStream.Qt_4_6)

        outstr.writeString(str(data))

        self.socket.write(block)

        if not self.socket.waitForBytesWritten(self.MAX_WRITE_RESPONSE_TIME):
            self.logger.error(
                f'Could not write to socket: {self.socket.errorString()}'
            )
        else:
            self.logger.debug(f'Sent data ok. {self.socket.state()}')

    def _on_ready_read(self):
        if not self._receiving:
            self._receive()

    def _receive(self):
        self.logger.debug('Receiving data ... ')

        stream = QtCore.QDataStream(self.socket)
        stream.setVersion(QtCore.QDataStream.Qt_4_6)

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
        '''
        Load and process incoming event

        :param raw_event:
        :return:
        '''
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

        # Is someone waiting for a reply
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
            self.on_run_dialog_callback(
                event['data']['dialog_name'],
                event['data']['tool_configs'],
            )
            self.send_reply(event, {})

    def send(
        self, topic, event_data, in_reply_to_event=None, synchronous=False
    ):
        '''Send an event to the DCC'''
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
            self.reply_event = None

            def handle_reply_event(topic, event_data, id):
                self.logger.info(
                    f'Registering incoming reply event: {topic} ({id}), '
                    f'data: {event_data}'
                )
                self.reply_event = event

            self._reply_id = event['id']
            self._handle_reply_event_callback = handle_reply_event

            timeout = self.REPLY_WAIT_TIMEOUT
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

                    if timeout <= waited:
                        raise Exception(
                            f'Timeout waiting for reply for event: {event["id"]}'
                        )
                    elif waited % 2000 == 0:
                        self.logger.info(
                            f'Waited {int(waited / 1000)}s for reply...'
                        )

                    if self.reply_event:
                        return self.reply_event

            finally:
                self._handle_reply_event_callback = None
                self._reply_id = None

    def send_reply(self, event, data):
        '''Send a reply to an event back to DCC'''
        self.send(event['topic'], data, in_reply_to_event=event['id'])

    def rpc(self, function_name, args=None):
        '''
        Send a remote procedure call to the DCC and return the result.

        :param function_name: The function to execute
        :param args: The arguments to pass
        execute async.
        :return: The result return from DCC.
        '''

        data = {
            'remote_integration_session_id': self.remote_integration_session_id,
            'function_name': function_name,
            'args': args or [],
        }

        self.logger.debug(f'Running {self.dcc_name.title()} RPC call: {data}')

        event_topic = constants.event.REMOTE_INTEGRATION_RPC_TOPIC

        result = self.send(event_topic, data, None, True)['result']

        self.logger.debug(
            f'Got {self.dcc_name.title()} RPC response: {result}'
        )

        return result

    def error(self, socketError):
        if (
            socketError
            == QtNetwork.QAbstractSocket.SocketError.RemoteHostClosedError
        ):
            self.logger.error('Host closed the connection...')
        elif (
            socketError
            == QtNetwork.QAbstractSocket.SocketError.HostNotFoundError
        ):
            self.logger.error(
                'The host was not found. Please check the host name and '
                'port settings.'
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
        self.socket.abort()

    def _on_disconnected(self):
        self.logger.warning(
            f'Connection to Harmony lost, terminating integration'
        )
        sys.exit(0)
