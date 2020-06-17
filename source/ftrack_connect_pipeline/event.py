# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import threading

import logging
import ftrack_api
from ftrack_connect_pipeline import constants
import uuid
logger = logging.getLogger(__name__)


class EventManager(object):
    '''Manages the events handling.'''

    def __repr__(self):
        return '<EventManager:{}:{}>'.format(self.mode, uuid.uuid4().hex)

    def __del__(self):
        self.logger.debug('Closing {}'.format(self))

    @property
    def session(self):
        return self._session

    @property
    def connected(self):
        _connected = False
        self.logger.debug(" on connected")
        try:
            _connected = self.session.event_hub.connected
        except Exception, e:
            self.logger.debug("Error checking connected --> {}".format(e))
        return _connected

    @property
    def mode(self):
        return self._mode

    def _connect(self):
        # If is not already connected, connect to event hub.
        self.logger.debug(" on connect")
        self.logger.debug(" self.connected {}".format(self.connected))
        while not self.connected:
            self.logger.debug(" on connect while")
            self.logger.debug('connecting to event hub')
            self.session.event_hub.connect()
            self.logger.debug(" after event hub connect")

    def _wait(self):
        self.logger.debug('On waiting')
        self._event_hub_thread = _EventHubThread()
        self.logger.debug("thread loaded")
        self._event_hub_thread.start(self.session)
        self.logger.debug("thread started")

    def __init__(self, session, mode=constants.LOCAL_EVENT_MODE):
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.logger.debug("initializing thread")
        self._mode = mode
        self.logger.debug("set mode")
        self._session = session
        self.logger.debug( "set session --> {}".format(session))
        self.logger.debug("self.session --> {}".format(self.session))

        self._connect()
        self.logger.debug("connect")
        self._wait()
        self.logger.debug("wait")

        self.logger.debug('Initialising {}'.format(self))

    def publish(self, event, callback=None, mode=None):
        '''Emit *event* and provide *callback* function.'''

        mode = mode or self.mode
        self.logger.debug(
            'Publishing event topic {} in {} mode'.format(
                event.get('topic'), mode
            )
        )
        if mode is constants.LOCAL_EVENT_MODE:

            result = self.session.event_hub.publish(
                event,
                synchronous=True,
            )

            if result:
                result = result[0]

            # Mock async event reply.
            new_event = ftrack_api.event.base.Event(
                topic=u'ftrack.meta.reply',
                data=result,
                in_reply_to_event=event['id'],
            )

            if callback:
                callback(new_event)

        else:
            self.session.event_hub.publish(
                event,
                on_reply=callback
            )

    def subscribe(self, topic, callback):
        self.session.event_hub.subscribe(
            'topic={}'.format(
                topic
            ),
            callback
        )


class _EventHubThread(threading.Thread):
    '''Listen for events from ftrack's event hub.'''

    def __init__(self):
        super(_EventHubThread, self).__init__()
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

    def start(self, session):
        '''Start thread for *_session*.'''
        self._session = session
        super(_EventHubThread, self).start()

    def run(self):
        '''Listen for events.'''
        self._session.event_hub.wait()
