# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging
from ftrack_connect_pipeline.host import Host
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_harmony import constants as harmony_constants
from ftrack_connect_pipeline_harmony.host import engine as host_engine

logger = logging.getLogger(__name__)


class HarmonyHost(Host):
    '''
    HarmonyHost class.
    '''

    host_types = [qt_constants.HOST_TYPE, harmony_constants.HOST_TYPE]
    # Define the Harmony engines to be run during the run function
    engines = {
        'asset_manager': host_engine.HarmonyAssetManagerEngine,
        'loader': host_engine.HarmonyLoaderEngine,
        'opener': host_engine.HarmonyOpenerEngine,
        'publisher': host_engine.HarmonyPublisherEngine,
    }

    def __init__(self, event_manager):
        '''
        Initialize HarmonyHost with *event_manager*.

        *event_manager* instance of
        :class:`ftrack_connect_pipeline.event.EventManager`
        '''
        super(HarmonyHost, self).__init__(event_manager)

    def run(self, event):
        runnerResult = super(HarmonyHost, self).run(event)
        return runnerResult
