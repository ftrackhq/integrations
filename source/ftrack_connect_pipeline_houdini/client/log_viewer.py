# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline_qt.client import log_viewer


class HoudiniQtLogViewerClientWidget(log_viewer.QtLogViewerClientWidget):
    '''Houdini log viewer dialog'''

    def __init__(self, event_manager, parent=None):
        super(HoudiniQtLogViewerClientWidget, self).__init__(event_manager)

        # Make sure we stays on top of Houdini
        self.setWindowFlags(QtCore.Qt.Tool)
