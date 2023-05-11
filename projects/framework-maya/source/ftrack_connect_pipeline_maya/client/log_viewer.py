# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline_qt.client import log_viewer


class MayaQtLogViewerClientWidget(log_viewer.QtLogViewerClientWidget):
    '''Maya log viewer dialog'''

    def __init__(self, event_manager, parent=None):
        super(MayaQtLogViewerClientWidget, self).__init__(event_manager)

        # Make sure we stays on top of Maya
        self.setWindowFlags(QtCore.Qt.Tool)
