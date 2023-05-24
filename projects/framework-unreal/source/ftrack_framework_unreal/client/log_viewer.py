# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore

from ftrack_framework_qt.client import log_viewer


class UnrealQtLogViewerClientWidget(log_viewer.QtLogViewerClientWidget):
    '''Unreal log viewer dialog'''

    def __init__(self, event_manager, parent=None):
        super(UnrealQtLogViewerClientWidget, self).__init__(event_manager)

        # Make sure we become a proper window
        self.setWindowFlags(QtCore.Qt.Window)
