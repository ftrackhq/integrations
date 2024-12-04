# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import threading

import logging

logger = logging.getLogger(__name__)


class EventHubThread(threading.Thread):
    '''Listen for events from ftrack's event hub.'''

    def __repr__(self):
        return "<{0}:{1}>".format(self.__class__.__name__, self.name)

    def __init__(self, session):
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        _name = str(hash(session))
        super(EventHubThread, self).__init__(name=_name)
        self.logger.debug(
            f'Initializing new EventHubThread for session {session}'
        )
        self.logger.debug(f'Name set for the thread: {_name}')
        self._session = session

    def start(self):
        '''Start thread for *_session*.'''
        self.logger.debug(
            f'Starting EventHubThread for session {self._session}'
        )
        super(EventHubThread, self).start()

    def run(self):
        '''Listen for events.'''
        self.logger.debug(
            f'EventHubThread started for session {self._session}'
        )
        self._session.event_hub.wait()
