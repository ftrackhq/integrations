# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import logging
from ftrack_connect_pipeline.host import Host
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_maya import constants as maya_constants
from ftrack_connect_pipeline_maya.host import engine as host_engine

logger = logging.getLogger(
    __name__
)

class MayaHost(Host):
    host = [qt_constants.HOST, maya_constants.HOST]
    engines = {
        'asset_manager': host_engine.MayaAssetManagerEngine,
        'loader': host_engine.LoaderEngine,
        'publisher': host_engine.PublisherEngine,
    }

    def __init__(self, event_manager):
        super(MayaHost, self).__init__(event_manager)

    def run(self, event):
        runnerResult = super(MayaHost, self).run(event)
        return runnerResult
