# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline_qt.client.log_viewer import QtLogViewerDialog

from ftrack_connect_pipeline_maya.utils.custom_commands import get_maya_window


class MayaLogViewerDialog(QtLogViewerDialog):
    '''Maya log viewer dialog'''

    def __init__(self, event_manager, unused_asset_list_model, parent=None):
        super(MayaLogViewerDialog, self).__init__(
            event_manager, parent=get_maya_window()
        )
