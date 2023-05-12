# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline_3dsmax.constants.asset import modes as load_const

from ftrack_connect_pipeline_qt.client import load
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_3dsmax.constants as max_constants
from ftrack_connect_pipeline_3dsmax import utils as max_utils


class MaxQtAssemblerClientWidget(load.QtAssemblerClientWidget):
    '''Max assembler dialog'''

    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        max_constants.UI_TYPE,
    ]

    def __init__(self, event_manager, asset_list_model, parent=None):
        super(MaxQtAssemblerClientWidget, self).__init__(
            event_manager,
            load_const.LOAD_MODES,
            asset_list_model,
            multithreading_enabled=False,
            parent=parent or max_utils.get_main_window(),
        )

        # Make sure we stays on top of Max
        self.setWindowFlags(QtCore.Qt.Tool)
