# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging
from framework_core.host import Host
from framework_qt import constants as qt_constants
from framework_unreal import constants as unreal_constants
from framework_unreal.host import engine as host_engine

logger = logging.getLogger(__name__)


class UnrealHost(Host):
    '''
    UnrealHost class.
    '''

    host_types = [qt_constants.HOST_TYPE, unreal_constants.HOST_TYPE]
    # Define the Unreal engines to be run during the run function
    engines = {
        'asset_manager': host_engine.UnrealAssetManagerEngine,
        'loader': host_engine.UnrealLoaderEngine,
        'publisher': host_engine.UnrealPublisherEngine,
    }

    def __init__(self, event_manager):
        '''
        Initialize UnrealHost with *event_manager*.

        *event_manager* instance of
        :class:`framework_core.event.EventManager`
        '''
        super(UnrealHost, self).__init__(event_manager)

    def run(self, event):
        runnerResult = super(UnrealHost, self).run(event)
        return runnerResult
