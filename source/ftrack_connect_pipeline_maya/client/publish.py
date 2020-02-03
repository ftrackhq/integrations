from ftrack_connect_pipeline_qt.client.publish import QtPublisherClient
from ftrack_connect_pipeline_maya.constants import HOST, UI

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin


class MayaPublisherClient(MayaQWidgetDockableMixin, QtPublisherClient):
    '''Dockable maya load widget'''
    def __init__(self, event_manager, parent=None):
        super(MayaPublisherClient, self).__init__(
            event_manager=event_manager, ui=['maya'], parent=parent
        )
        self.setWindowTitle('Maya Pipeline Publisher')

    def show(self):
        super(MayaPublisherClient, self).show(
            dockable=True, floating=False, area='right',
            width=200, height=300, x=300, y=600
    )
