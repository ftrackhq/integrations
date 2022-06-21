# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtWidgets, QtCompat, QtCore

from ftrack_connect_pipeline_nuke.constants.asset import modes as load_const

from ftrack_connect_pipeline_qt.client import load
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_nuke.constants as nuke_constants
from ftrack_connect_pipeline_nuke.utils.custom_commands import get_main_window


class NukeQtAssemblerClientWidget(load.QtAssemblerClientWidget):
    '''Nuke assembler dialog'''

    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        nuke_constants.UI_TYPE,
    ]

    assembler_match_extension = (
        True  # Allow nuke to resolve assets in a more relaxed way
    )

    def __init__(self, event_manager, asset_list_model, parent=None):
        super(NukeQtAssemblerClientWidget, self).__init__(
            event_manager,
            load_const.LOAD_MODES,
            asset_list_model,
            parent=(parent or get_main_window()),
        )
        # Make toolbar smaller
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, False)

    def closeEvent(self, event):
        '''Nuke deletes the dialog, instead hide so it can be reused'''
        self.setVisible(False)
        event.ignore()
