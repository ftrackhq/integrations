from ftrack_connect_pipeline_qt.client.load import QtLoaderClient
from ftrack_connect_pipeline_maya.constants import HOST, UI

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin


class MayaLoaderClient(MayaQWidgetDockableMixin, QtLoaderClient):
    '''Dockable maya load widget'''
    def __init__(self, event_manager, parent=None):
        super(MayaLoaderClient, self).__init__(
            event_manager, ui=['maya'], parent=parent
        )
        self.setWindowTitle('Maya Pipeline Loader')

    def show(self):
        super(MayaLoaderClient, self).show(
            dockable=True, floating=False, area='right',
            width=200, height=300, x=300, y=600
    )