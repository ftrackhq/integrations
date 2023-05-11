# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline_qt.client import open
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_nuke.constants as nuke_constants


class NukeQtOpenerClientWidget(open.QtOpenerClientWidget):
    '''Nuke open dialog'''

    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        nuke_constants.UI_TYPE,
    ]
    definition_extensions_filter = ['.nk']

    def __init__(self, event_manager, parent=None):
        super(NukeQtOpenerClientWidget, self).__init__(event_manager)
        # Make toolbar smaller
        self.setWindowFlags(QtCore.Qt.Tool)

    def closeEvent(self, event):
        '''Nuke deletes the dialog, instead hide it so it can be reused'''
        self.setVisible(False)
        event.ignore()
