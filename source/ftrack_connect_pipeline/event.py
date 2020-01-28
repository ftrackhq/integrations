# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import threading

import logging
import ftrack_api
from ftrack_connect_pipeline import session, constants
logger = logging.getLogger(__name__)


class _EventThread(threading.Thread):
    '''Wrapper object to simulate asyncronus events.'''
    def __init__(self, session, event, callback=None):
        super(_EventThread, self).__init__(target=self.run)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self._callback = callback
        self._event = event
        self._session = session
        self._result = {}

    def run(self):
        '''Target thread method.'''
        result = self._session.event_hub.publish(
            self._event,
            synchronous=True,
        )

        if result:
            result = result[0]

        # Mock async event reply.
        event = ftrack_api.event.base.Event(
            topic=u'ftrack.meta.reply',
            data=result,
            in_reply_to_event=self._event['id'],
        )

        if self._callback:
            self._callback(event)


class EventManager(object):
    '''Manages the events handling.'''


    @property
    def connected(self):
        return self.session.event_hub.connected

    def __init__(self, session, mode=constants.LOCAL_EVENT_MODE, deamon=True):
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.mode = mode
        self.session = session

        # If is not already connected, connect to event hub.
        while not self.session.event_hub.connected:
            self.logger.info('connecting to event hub')
            self.session.event_hub.connect()

        self._event_hub_thread = _EventHubThread()
        self._event_hub_thread.daemon = deamon
        self._event_hub_thread.start(self.session)

    def publish(self, event, callback=None, mode=None):
        '''Emit *event* and provide *callback* function.'''

        mode = mode or self.mode
        if mode is constants.LOCAL_EVENT_MODE:
            event_thread = _EventThread(self.session, event, callback)
            event_thread.start()
            event_thread.join()

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
        self.logger.info('Starting event hub thread.')
        super(_EventHubThread, self).start()

    def run(self):
        '''Listen for events.'''
        self.logger.info('Event hub thread started.')
        self._session.event_hub.wait()
