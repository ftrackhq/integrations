from ftrack_framework_core.event import EventManager


class QEventManager(EventManager):
    '''QT wrapper for pipeline event manager'''

    def _wait(self):
        pass
