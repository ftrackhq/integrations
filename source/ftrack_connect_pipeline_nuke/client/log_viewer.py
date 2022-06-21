# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtCore

from ftrack_connect_pipeline_qt.client import log_viewer
from ftrack_connect_pipeline_nuke.utils.custom_commands import get_main_window


class NukeQtLogViewerClientWidget(log_viewer.QtLogViewerClientWidget):

    '''Nuke log viewer dialog'''

    def __init__(self, event_manager, parent=None):
        super(NukeQtLogViewerClientWidget, self).__init__(
            event_manager=event_manager,
            parent=(parent or get_main_window()),
        )
        # Make toolbar smaller
        self.setWindowFlags(QtCore.Qt.Tool)

