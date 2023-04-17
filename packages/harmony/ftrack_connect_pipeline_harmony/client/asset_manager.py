# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_connect_pipeline_qt.client.asset_manager import (
    QtAssetManagerClientWidget,
)
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_harmony.constants as harmony_constants


class HarmonyQtAssetManagerClientWidget(QtAssetManagerClientWidget):
    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        harmony_constants.UI_TYPE,
    ]
    '''Dockable harmony asset manager widget'''

    def __init__(self, event_manager, asset_list_model, parent=None):
        super(HarmonyQtAssetManagerClientWidget, self).__init__(
            event_manager, asset_list_model, parent=parent
        )
        self.setWindowTitle('Harmony Pipeline Asset Manager')

    def get_theme_background_style(self):
        return 'harmony'
