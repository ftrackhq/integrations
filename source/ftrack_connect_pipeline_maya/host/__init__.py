# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import logging
import ftrack_api
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_maya import constants as maya_constants
from ftrack_connect_pipeline.host import Host
from ftrack_connect_pipeline_maya.host.engine.asset_manager import MayaAssetManagerEngine

logger = logging.getLogger(
    __name__
)

class MayaHost(Host):
    host = [qt_constants.HOST, maya_constants.HOST]
    asset_manager_engine = MayaAssetManagerEngine

    def run(self, event):
        super(MayaHost, self).run(event)
        self._refresh_asset_manager()

    def _refresh_asset_manager(self):
        event = ftrack_api.event.base.Event(
            topic=qt_constants.PIPELINE_REFRESH_AM,
            data={
                'pipeline': {
                    'host_id': self.hostid,
                    'data': {},
                }
            }
        )
        self._event_manager.publish(event)
