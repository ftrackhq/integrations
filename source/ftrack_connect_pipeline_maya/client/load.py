# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline_maya.constants.asset import modes as load_const

from ftrack_connect_pipeline_qt.client import load
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_maya.constants as maya_constants
from ftrack_connect_pipeline_maya.utils.custom_commands import get_main_window


class MayaAssemblerWidget(load.QtAssemblerWidget):
    '''Maya assembler dialog'''

    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        maya_constants.UI_TYPE,
    ]

    def __init__(self, event_manager, asset_list_model, parent=None):
        super(MayaAssemblerWidget, self).__init__(
            event_manager,
            load_const.LOAD_MODES,
            asset_list_model,
            parent=(parent or get_main_window()),
        )

        # Make sure we stays on top of Maya
        self.setWindowFlags(QtCore.Qt.Tool)

    def show(self):
        super(MayaAssemblerWidget, self).conditional_rebuild()
        super(MayaAssemblerWidget, self).show()
