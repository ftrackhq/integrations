import logging

from Qt import QtWidgets, QtCore, QtGui

from ftrack_connect_pipeline.event import EventManager


class _QEventHubThread(QtCore.QThread):

    def __init__(self):
        super(_QEventHubThread, self).__init__()
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

    def start(self, session):
        '''Start thread for *_session*.'''
        self._session = session
        self.logger.info('Starting event hub thread.')
        super(_QEventHubThread, self).start()

    def run(self):
        '''Listen for events.'''
        self.logger.info('Event hub thread started.')
        self._session.event_hub.wait()


class QEventManager(EventManager):
    def _wait(self):
        pass
        # self._event_hub_thread = _QEventHubThread()
        # self._event_hub_thread.start(self.session)

