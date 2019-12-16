# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import threading

import logging
import ftrack_api
from ftrack_connect_pipeline import session, constants
logger = logging.getLogger(__name__)

from Qt import QtCore


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
    def __init__(self, mode=constants.LOCAL_EVENT_MODE):
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.mode = mode
        self.session = session.get_shared_session()
        self._event_hub_thread = _EventHubThread()
        self._event_hub_thread.start(self.session)

    def publish(self, event, callback=None, force_mode=None):
        '''Emit *event* and provide *callback* function.'''

        mode = force_mode or self.mode
        if mode is constants.LOCAL_EVENT_MODE:
            event_thread = _EventThread(self.session, event, callback)
            event_thread.start()

        else:
            self.session.event_hub.publish(
                event,
                on_reply=callback
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
        self.logger.debug('Starting event hub thread.')
        super(_EventHubThread, self).start()

    def run(self):
        '''Listen for events.'''
        self.logger.debug('Event hub thread started.')
        self._session.event_hub.wait()
