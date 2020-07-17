# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import logging
import ftrack_api
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_nuke import constants as nuke_constants
from ftrack_connect_pipeline.host import Host
from ftrack_connect_pipeline_nuke.host.engine.asset_manager import NukeAssetManagerEngine


logger = logging.getLogger(
    __name__
)


class NukeHost(Host):
    host = [qt_constants.HOST, nuke_constants.HOST]
    asset_manager_engine = NukeAssetManagerEngine

    def run(self, event):
        super(NukeHost, self).run(event)
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
