# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline_qt.client import log_viewer

from ftrack_connect_pipeline_3dsmax import utils as max_utils


class MaxQtLogViewerClientWidget(log_viewer.QtLogViewerClientWidget):
    '''Max log viewer dialog'''

    def __init__(self, event_manager, parent=None):
        super(MaxQtLogViewerClientWidget, self).__init__(
            event_manager, parent=max_utils.get_main_window()
        )

        # Make sure we stay on top of Max
        self.setWindowFlags(QtCore.Qt.Tool)
