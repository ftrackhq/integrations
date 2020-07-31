# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import logging
import ftrack_api

from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_3dsmax import constants as max_constants
from ftrack_connect_pipeline.host import Host
from ftrack_connect_pipeline_3dsmax.host.engine.asset_manager import MaxAssetManagerEngine

logger = logging.getLogger(__name__)


class MaxHost(Host):
    host = [qt_constants.HOST, max_constants.HOST]

    def run(self, event):
        runnerResult = super(MaxHost, self).run(event)
        return runnerResult
