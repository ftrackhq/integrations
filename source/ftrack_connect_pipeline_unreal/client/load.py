# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtWidgets, QtCore


from ftrack_connect_pipeline import constants as core_constants


from ftrack_connect_pipeline_qt.client import load
import ftrack_connect_pipeline_qt.constants as qt_constants

from ftrack_connect_pipeline_unreal.constants.asset import modes as load_const
import ftrack_connect_pipeline_unreal.constants as unreal_constants


class UnrealQtAssemblerClientWidget(load.QtAssemblerClientWidget):
    '''Unreal assembler dialog'''

    ui_types = [
        core_constants.UI_TYPE,
        qt_constants.UI_TYPE,
        unreal_constants.UI_TYPE,
    ]

    def __init__(
        self,
        event_manager,
        asset_list_model,
        parent=None,
    ):
        super(UnrealQtAssemblerClientWidget, self).__init__(
            event_manager,
            load_const.LOAD_MODES,
            asset_list_model,
            multithreading_enabled=False,
        )

        # Make sure we stays on top of Unreal
        self.setWindowFlags(QtCore.Qt.Window)
