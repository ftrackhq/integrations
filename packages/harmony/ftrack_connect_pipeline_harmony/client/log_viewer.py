# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline_qt.client import log_viewer

from ftrack_connect_pipeline_harmony import utils as harmony_utils


class HarmonyQtLogViewerClientWidget(log_viewer.QtLogViewerClientWidget):
    '''Harmony log viewer dialog'''

    def __init__(self, event_manager, parent=None):
        super(HarmonyQtLogViewerClientWidget, self).__init__(event_manager)

        # Make sure we stays on top of Harmony
        self.setWindowFlags(QtCore.Qt.Tool)
