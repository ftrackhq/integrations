# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from framework_qt.client.asset_manager import (
    QtAssetManagerClientWidget,
)
import framework_core.constants as constants
import framework_qt.constants as qt_constants

import framework_unreal.constants as unreal_constants


class UnrealQtAssetManagerClientWidget(QtAssetManagerClientWidget):
    '''Dockable unreal asset manager widget'''

    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        unreal_constants.UI_TYPE,
    ]

    snapshot_assets = True

    def __init__(
        self,
        event_manager,
        asset_list_model,
        is_assembler=False,
        multithreading_enabled=False,
        parent=None,
    ):
        super(UnrealQtAssetManagerClientWidget, self).__init__(
            event_manager,
            asset_list_model,
            is_assembler=is_assembler,
            multithreading_enabled=multithreading_enabled,
            parent=parent,
        )
        self.setWindowTitle('Unreal Pipeline Asset Manager')
        self.resize(600, 800)

    def get_theme_background_style(self):
        return 'ftrack' if not self.is_assembler else 'transparent'

    def is_docked(self):
        return False
