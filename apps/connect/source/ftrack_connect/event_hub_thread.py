# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_connect.qt import QtCore


class NewApiEventHubThread(QtCore.QThread):
    '''Listen for events from ftrack's event hub.'''

    def start(self, session):
        '''Start thread for *session*.'''
        self._session = session
        super(NewApiEventHubThread, self).start()

    def run(self):
        '''Listen for events.'''
        while not self.isInterruptionRequested():
            self._session.event_hub.wait(duration=0)

    def quit(self):
        '''Signal the run method to exit after the next loop.'''
        self.requestInterruption()

    def cleanup(self):
        '''Attempt to kill the event loop and return after it completes.'''
        self.quit()
        self.wait()
