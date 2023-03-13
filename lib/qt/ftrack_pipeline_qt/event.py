from ftrack_connect_pipeline.event import EventManager


class QEventManager(EventManager):
    '''QT wrapper for pipeline event manager'''

    def _wait(self):
        pass
