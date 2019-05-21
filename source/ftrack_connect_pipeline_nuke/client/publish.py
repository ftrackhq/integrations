from ftrack_connect_pipeline.client.publish import QtPipelinePublishWidget
from ftrack_connect_pipeline_nuke.constants import HOST, UI


class QtPipelineNukePublisherWidget(QtPipelinePublishWidget):
    '''Dockable nuke load widget'''
    def __init__(self, hostid, parent=None):
        super(QtPipelineNukePublisherWidget, self).__init__(host=HOST, ui=UI, hostid=hostid, parent=parent)
        self.setWindowTitle('Nuke Pipeline Publisher')
