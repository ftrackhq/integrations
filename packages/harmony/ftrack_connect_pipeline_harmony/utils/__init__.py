# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import json
import time
import logging
import uuid

from Qt import QtWidgets, QtCore, QtGui, QtNetwork

import ftrack_api

from ftrack_connect_pipeline import host, constants, event

### COMMON UTILS ###

logger = logging.getLogger(__name__)

event_hub_client = None

def run_in_main_thread(f):
    '''Make sure a function runs in the main Harmony thread.'''

    @wraps(f)
    def decorated(*args, **kwargs):
        if threading.currentThread().name != 'MainThread':
            pass
        else:
            return f(*args, **kwargs)

    return decorated

def store_client(_event_hub_client):
    global event_hub_client

    event_hub_client = _event_hub_client

def get_event_hub_client():
    return event_hub_client


class TCPEventHubClient(QtCore.QObject):
    MAX_WRITE_RESPONSE_TIME = 10000
    INT32_SIZE = 4
    REPLY_WAIT_TIMEOUT_S = 60

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def session_id(self):
        return self._session_id

    def __init__(self, host, port, _integration_session_id, handle_event_callback, parent=None):
        super(TCPEventHubClient, self).__init__(parent=parent)

        self._parent = parent
        self._host = host
        self._port = port
        self._session_id = _integration_session_id
        self._handle_event_callback = handle_event_callback
        self._handle_reply_event_callback = None
        self._blocksize = 0

        self._callbacks = {}
        self.responses = {}
        self.awaiting_response = []

        self.connection = QtNetwork.QTcpSocket(self)
        self.connection.connected.connect(self._on_connected)
        self._buffer = None
        self._receiving = False

        logger.info("Initialized event hub client");

    def connection_status(self):
        return self.connection.state()

    def is_connected(self):
        return self.connection and (
                self.connection_status() == QtNetwork.QAbstractSocket.ConnectedState
        )

    def connect(self):
        logger.info("Connecting to event hub @ %s:%s " % (self.host, self.port))

        if self.is_connected():
            logger.warning(
                "Connection already existed , removing connection to %s %s " % (self.host, self.port)
            )
            self.connection.abort()

        st2 = time.time()
        self.connection.connectToHost(self.host, self.port)

        if not self.connection.waitForConnected(1500):
            et2 = time.time()
            logger.error("Error connecting to the event hub (%s s)" % (et2 - st2))
            return self.connection_status()
        else:
            et2 = time.time()
            logger.debug("Connected (%s s)" % (et2 - st2))

        result = self.connection_status()
        logger.debug("Connect status: %s", result)

        logger.info("Connected to event hub @ {}:{}".format(self.host, self.port))

        # commands = self.send_and_receive_command("DIR")
        # logger.debug("commands: %s" % commands)

        return result

    def _on_readyRead(self):
        logger.warning("Ready to read")

    def _on_error(self):
        logger.debug("Error occurred: %s" % self.connection.errorString())

    def _on_bytes_written(self, bytes):
        logger.debug("Bytes written: %s" % bytes)

    def _on_state_changed(self, state):
        logger.debug("stateChanged: %s" % state)

    def _on_connected(self):
        logger.debug("On connected to event hub called.")
        logger.debug("Connection: %s" % self.connection)

        logger.debug("Setting up connection options...")
        self.connection.setSocketOption(self.connection.LowDelayOption, 1)
        self.connection.setSocketOption(self.connection.KeepAliveOption, 1)

        self.connection.readyRead.connect(self._on_ready_read)
        self.connection.error.connect(self._on_error)
        self.connection.bytesWritten.connect(self._on_bytes_written)
        self.connection.stateChanged.connect(self._on_state_changed)

    def _send(self, data):
        # make sure we are connected
        if self.connection.state() in (
                QtNetwork.QAbstractSocket.SocketState.UnconnectedState,
        ):
            self.connect()

        block = QtCore.QByteArray()

        outstr = QtCore.QDataStream(block, QtCore.QIODevice.WriteOnly)
        outstr.setVersion(QtCore.QDataStream.Qt_4_6)

        outstr.writeString(str(data))

        self.connection.write(block)

        if not self.connection.waitForBytesWritten(self.MAX_WRITE_RESPONSE_TIME):
            logger.error("Could not write to socket: %s" % self.connection.errorString())
        else:
            logger.debug("Sent data ok. %s" % self.connection.state())

    def _on_ready_read(self):
        if not self._receiving:
            self._receive()

    def _receive(self):
        logger.debug("Receiving data ... ")

        stream = QtCore.QDataStream(self.connection)
        stream.setVersion(QtCore.QDataStream.Qt_4_6)

        i = 0
        while self.connection.bytesAvailable() > 0:
            if (self._blocksize == 0 and self.connection.bytesAvailable() >= self.INT32_SIZE) or (
                    self._blocksize > 0 and self.connection.bytesAvailable() >= self._blocksize
            ):
                self._blocksize = stream.readInt32()
                # logger.debug(
                #     "Reading data size for request %s in queue: %s"
                #     % (i, self._blocksize)
                # )

            if self._blocksize > 0 and self.connection.bytesAvailable() >= self._blocksize:
                data = stream.readRawData(self._blocksize)
                raw_event = QtCore.QTextCodec.codecForMib(106).toUnicode(data)
                # logger.debug("About to process request %s in queue: %s" % (i, request))
                self._decode_and_process_event(raw_event)
                self._blocksize = 0
                i += 1

        return None

    def _decode_and_process_event(self, raw_event):
        # make sure is a json like request
        logger.info("Decoding incoming event: {}".format(str(raw_event)))
        try:
            event = json.loads(raw_event)
        except Exception as e:
            logger.warning("Ignoring request, not well formed! Details: {}".format(e))
            return None

        # Is this event for us?
        event_data = event.get('data')
        if not event_data:
            logger.warning("Ignoring request, no data. %s", raw_event)
            return None

        session_id = event_data.get('integration_session_id')

        if session_id != self.session_id:
            logger.warning("Ignoring event, not for us. %s", raw_event)
            return None

        # Is someone waiting for a reply
        if self._handle_reply_event_callback:
            if event.get('in_reply_to_event') == self._reply_id:
                logger.info("Got reply for event: {}".format(self._reply_id))
                self._handle_reply_event_callback(event['topic'], event_data, event['id'])
                return None

        self._handle_event_callback(event['topic'], event_data, event['id'])

    def send(self, topic, event_data, synchronous=False):
        event = {
            'id': str(uuid.uuid4()),
            'topic': topic,
            'data': event_data,
        }
        st = time.time()
        self._send(json.dumps(event))
        et = time.time()
        logger.info("Sent {} event (took: {} secs): {}".format(topic, (et - st), event))

        if synchronous:

            self.reply_event = None

            def handle_reply_event(topic, event_data, id):
                logger.info('Registering incoming reply event: {} ({}), data: {}'.format(topic, id, event_data))
                self.reply_event = event

            self._reply_id = event['id']
            self._handle_reply_event_callback = handle_reply_event

            timeout = self.REPLY_WAIT_TIMEOUT_S
            try:
                logger.info("Waiting to receive reply for {}...".format(event['id']))

                time.sleep(0.1)
                timeout -= 0.1

                if timeout <= 0:
                    raise Exception("Timeout waiting for reply for event: {}".format(event['id']))

                if self.reply_event:
                    return self.reply_event

                QtGui.QApplication.processEvents()
            finally:
                # Deregister collback handler
                self._handle_reply_event_callback = None
                self._reply_id = None
    def error(self, socketError):
        if socketError == QtNetwork.QAbstractSocket.RemoteHostClosedError:
            logger.error("Host closed the connection...")
        elif socketError == QtNetwork.QAbstractSocket.HostNotFoundError:
            logger.error(
                "The host was not found. Please check the host name and " "port settings."
            )
        elif socketError == QtNetwork.QAbstractSocket.ConnectionRefusedError:
            logger.error("The server is not up and running yet.")
        else:
            logger.error("The following error occurred: %s." % self.connection.errorString())

    def close(self):
        self.connection.abort()



from ftrack_connect_pipeline_harmony.utils.file import *
from ftrack_connect_pipeline_harmony.utils.node import *