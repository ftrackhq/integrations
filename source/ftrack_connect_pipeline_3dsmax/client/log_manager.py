# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline_qt.client.log_manager import QtLogManagerClient
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_3dsmax.constants as max_constants



class MaxLogManagerClient(QtLogManagerClient):
    ui = [constants.UI, qt_constants.UI, max_constants.UI]

    '''Dockable maya load widget'''
    def __init__(self, event_manager, parent=None):
        super(MaxLogManagerClient, self).__init__(
            event_manager=event_manager, parent=parent
        )
        self.setWindowTitle('Nuke Pipeline Log Manager')

    def show(self):
        self.dock_widget.show()
        super(MaxLogManagerClient, self).show()
