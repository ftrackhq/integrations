# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging

from ftrack_framework_core import constants as core_constants
from ftrack_framework_qt import constants as qt_constants
from ftrack_framework_houdini import constants as houdini_constants
from ftrack_framework_core.host import Host
from ftrack_framework_houdini.host import engine as host_engine


logger = logging.getLogger(__name__)


class HoudiniHost(Host):
    host_types = [qt_constants.HOST_TYPE, houdini_constants.HOST_TYPE]

    # Define the Houdini engines to be run during the run function
    engines = {
        core_constants.PUBLISHER: host_engine.HoudiniPublisherEngine,
        core_constants.LOADER: host_engine.HoudiniLoaderEngine,
        core_constants.OPENER: host_engine.HoudiniOpenerEngine,
        core_constants.ASSET_MANAGER: host_engine.HoudiniAssetManagerEngine,
        core_constants.RESOLVER: host_engine.HoudiniResolverEngine,
    }

    def __init__(self, event_manager):
        '''
        Initialize HoudiniHost with *event_manager*.

        *event_manager* instance of
        :class:`ftrack_framework_core.event.EventManager`
        '''
        super(HoudiniHost, self).__init__(event_manager)

    def run(self, event):
        runnerResult = super(HoudiniHost, self).run(event)
        return runnerResult
