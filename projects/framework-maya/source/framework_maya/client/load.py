# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
from Qt import QtWidgets, QtCore

from framework_maya.constants.asset import modes as load_const

from framework_qt.client import load
import framework_core.constants as constants
import framework_qt.constants as qt_constants
import framework_maya.constants as maya_constants


class MayaQtAssemblerClientWidget(load.QtAssemblerClientWidget):
    '''Maya assembler dialog'''

    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        maya_constants.UI_TYPE,
    ]

    def __init__(self, event_manager, asset_list_model, parent=None):
        super(MayaQtAssemblerClientWidget, self).__init__(
            event_manager,
            load_const.LOAD_MODES,
            asset_list_model,
        )

        # Make sure we stays on top of Maya
        self.setWindowFlags(QtCore.Qt.Tool)
