from ftrack_connect_pipeline.client.load import QtPipelineLoaderWidget
from ftrack_connect_pipeline_nuke.constants import HOST, UI


class QtPipelinenukeLoaderWidget(QtPipelineLoaderWidget):
    '''Dockable nuke load widget'''
    def __init__(self, hostid, parent=None):
        super(QtPipelinenukeLoaderWidget, self).__init__(host=HOST, ui=UI, hostid=hostid, parent=parent)
        self.setWindowTitle('nuke Pipeline Loader{}'.format(hostid))
