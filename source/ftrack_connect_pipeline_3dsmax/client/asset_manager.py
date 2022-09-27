# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline_qt.client.asset_manager import (
    QtAssetManagerClientWidget,
)
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_3dsmax.constants as 3dsmax_constants


class MaxQtAssetManagerClientWidget(QtAssetManagerClientWidget):
    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        3dsmax_constants.UI_TYPE,
    ]
    '''Dockable 3dsmax asset manager widget'''

    def __init__(self, event_manager, asset_list_model, parent=None):
        super(MaxQtAssetManagerClientWidget, self).__init__(
            event_manager, asset_list_model, parent=parent
        )
        self.setWindowTitle('Max Pipeline Asset Manager')

    def get_theme_background_style(self):
        return '3dsmax'