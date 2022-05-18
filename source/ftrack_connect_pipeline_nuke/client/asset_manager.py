# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline_qt.client.asset_manager import (
    QtAssetManagerClient,
)
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_nuke.constants as nuke_constants
from ftrack_connect_pipeline_nuke.utils.custom_commands import get_main_window


class NukeAssetManagerClient(QtAssetManagerClient):
    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        nuke_constants.UI_TYPE,
    ]

    '''Dockable nuke asset manager widget'''

    def __init__(self, event_manager, asset_list_model):
        super(NukeAssetManagerClient, self).__init__(
            event_manager, asset_list_model, parent=get_main_window()
        )
        self.setWindowTitle('ftrack Connect')

    def get_theme_background_style(self):
        return 'nuke'

    def show(self):
        super(NukeAssetManagerClient, self).conditional_rebuild()
        super(NukeAssetManagerClient, self).show()
