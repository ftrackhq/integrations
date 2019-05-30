from ftrack_connect_pipeline.client.publish import QtPipelinePublishWidget
from ftrack_connect_pipeline_3dsmax.constants import HOST, UI


# TODO(spetterborg) Figure out whether we have one of these for max

class QtPipelineMaxPublishWidget(MaxQWidgetDockableMixin, QtPipelinePublishWidget):
    '''Dockable maya load widget'''
    def __init__(self, hostid, parent=None):
        super(QtPipelineMayaPublishWidget, self).__init__(host=HOST, ui=UI,hostid=hostid, parent=parent)
        self.setWindowTitle('Maya Pipeline Publisher')

    def show(self):
        super(QtPipelineMayaPublishWidget, self).show(
            dockable=True, floating=False, area='right',
            width=200, height=300, x=300, y=600
        )
