# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

from ftrack_framework_qt.client.asset_manager import (
    QtAssetManagerClientWidget,
)
import ftrack_framework_core.constants as constants
import ftrack_framework_qt.constants as qt_constants
import ftrack_framework_houdini.constants as houdini_constants


class HoudiniQtAssetManagerClientWidget(QtAssetManagerClientWidget):
    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        houdini_constants.UI_TYPE,
    ]
    '''Dockable houdini asset manager widget'''

    def __init__(self, event_manager, asset_list_model, parent=None):
        super(HoudiniQtAssetManagerClientWidget, self).__init__(
            event_manager, asset_list_model, parent=parent
        )
        self.setWindowTitle('Houdini Pipeline Asset Manager')

    def get_theme_background_style(self):
        return 'houdini'
