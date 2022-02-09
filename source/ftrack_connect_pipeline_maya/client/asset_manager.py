# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline_qt.client.asset_manager import (
    QtAssetManagerClient,
)
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_maya.constants as maya_constants

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin


class MayaAssetManagerClient(MayaQWidgetDockableMixin, QtAssetManagerClient):
    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        maya_constants.UI_TYPE,
    ]

    '''Dockable maya load widget'''

    def __init__(self, event_manager, asset_list_model, parent=None):
        super(MayaAssetManagerClient, self).__init__(
            event_manager=event_manager,
            asset_list_model=asset_list_model,
            parent=parent,
        )
        self.setWindowTitle('Maya Pipeline Asset Manager')

    def get_background_color(self):
        return 'maya'

    def show(self):
        super(MayaAssetManagerClient, self).show(
            dockable=True,
            floating=False,
            area='right',
            width=200,
            height=300,
            x=300,
            y=600,
        )
