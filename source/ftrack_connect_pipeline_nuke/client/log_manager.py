# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline_qt.client.log_manager import QtLogManagerClient
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_nuke.constants as nuke_constants


class NukeLogManagerClient(QtLogManagerClient):
    ui = [constants.UI, qt_constants.UI, nuke_constants.UI]

    '''Dockable maya load widget'''
    def __init__(self, event_manager, parent=None):
        super(NukeLogManagerClient, self).__init__(
            event_manager=event_manager, parent=parent
        )
        self.setWindowTitle('Nuke Pipeline Log Manager')