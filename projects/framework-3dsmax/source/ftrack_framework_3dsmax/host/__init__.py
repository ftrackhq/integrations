# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import logging

from ftrack_framework_core.host import Host
from ftrack_framework_core import constants as core_constants
from ftrack_framework_qt import constants as qt_constants
from ftrack_framework_3dsmax import constants as max_constants
from ftrack_framework_3dsmax.host import engine as host_engine

logger = logging.getLogger(__name__)


class MaxHost(Host):
    '''
    MaxHost class.
    '''

    host_types = [qt_constants.HOST_TYPE, max_constants.HOST_TYPE]
    # Define the Max engines to be run during the run function
    engines = {
        core_constants.PUBLISHER: host_engine.MaxPublisherEngine,
        core_constants.LOADER: host_engine.MaxLoaderEngine,
        core_constants.OPENER: host_engine.MaxOpenerEngine,
        core_constants.ASSET_MANAGER: host_engine.MaxAssetManagerEngine,
        core_constants.RESOLVER: host_engine.MaxResolverEngine,
    }

    def __init__(self, event_manager):
        '''
        Initialize MaxHost with *event_manager*.

        *event_manager* instance of
        :class:`ftrack_framework_core.event.EventManager`
        '''
        super(MaxHost, self).__init__(event_manager)

    def run(self, event):
        runnerResult = super(MaxHost, self).run(event)
        return runnerResult
