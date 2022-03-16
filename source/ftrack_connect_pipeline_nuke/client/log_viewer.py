# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtWidgets

from ftrack_connect_pipeline_qt.client.log_viewer import QtLogViewerDialog


class NukeLogViewerDialog(QtLogViewerDialog):

    '''Nuke log viewer dialog'''

    def __init__(self, event_manager, unused_asset_list_model, parent=None):
        super(NukeLogViewerDialog, self).__init__(
            event_manager=event_manager,
            parent=parent or QtWidgets.QApplication.activeWindow(),
        )
