# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

from ftrack_connect_pipeline_qt.client.asset_manager import (
    QtAssetManagerClient,
)
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_houdini.constants as houdini_constants


class HoudiniAssetManagerClient(QtAssetManagerClient):
    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        houdini_constants.UI_TYPE,
    ]
    '''Dockable houdini load widget'''

    def __init__(self, event_manager, parent=None):
        super(HoudiniAssetManagerClient, self).__init__(
            event_manager=event_manager, parent=parent
        )
        self.setWindowTitle('Houdini Pipeline Asset Manager')
