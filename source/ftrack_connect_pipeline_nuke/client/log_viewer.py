# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtCore

from ftrack_connect_pipeline_qt.client.log_viewer import QtLogViewerDialog
from ftrack_connect_pipeline_nuke.utils.custom_commands import get_nuke_window


class NukeLogViewerDialog(QtLogViewerDialog):

    '''Nuke log viewer dialog'''

    def __init__(self, event_manager, unused_asset_list_model, parent=None):
        super(NukeLogViewerDialog, self).__init__(
            event_manager=event_manager,
            parent=parent or get_nuke_window(),
        )

        self.setWindowFlags(QtCore.Qt.Tool)
