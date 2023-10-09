# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging
from ftrack_framework_core.host import Host
from ftrack_framework_core import constants as core_constants
from ftrack_framework_qt import constants as qt_constants
from ftrack_framework_unreal import constants as unreal_constants
from ftrack_framework_unreal.host import engine as host_engine

logger = logging.getLogger(__name__)


class UnrealHost(Host):
    '''
    UnrealHost class.
    '''

    host_types = [qt_constants.HOST_TYPE, unreal_constants.HOST_TYPE]
    # Define the Unreal engines to be run during the run function
    engines = {
        core_constants.PUBLISHER: host_engine.UnrealPublisherEngine,
        core_constants.LOADER: host_engine.UnrealLoaderEngine,
        core_constants.ASSET_MANAGER: host_engine.UnrealAssetManagerEngine,
        core_constants.RESOLVER: host_engine.UnrealResolverEngine,
    }

    def __init__(self, event_manager):
        '''
        Initialize UnrealHost with *event_manager*.

        *event_manager* instance of
        :class:`ftrack_framework_core.event.EventManager`
        '''
        super(UnrealHost, self).__init__(event_manager)

    def run(self, event):
        runnerResult = super(UnrealHost, self).run(event)
        return runnerResult
