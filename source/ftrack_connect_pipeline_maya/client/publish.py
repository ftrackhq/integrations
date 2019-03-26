from ftrack_connect_pipeline.client.publish import QtPipelinePublishWidget
from ftrack_connect_pipeline_maya.constants import HOST, UI

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin


class QtPipelineMayaPublishWidget(MayaQWidgetDockableMixin, QtPipelinePublishWidget):
    '''Dockable maya load widget'''
    def __init__(self, hostid, parent=None):
        super(QtPipelineMayaPublishWidget, self).__init__(host=HOST, ui=UI,hostid=hostid, parent=parent)
        self.setWindowTitle('Maya Pipeline Publisher:{}'.format(hostid))

    def show(self):
        super(QtPipelineMayaPublishWidget, self).show(
            dockable=True, floating=False, area='right',
            width=200, height=300, x=300, y=600
    )
