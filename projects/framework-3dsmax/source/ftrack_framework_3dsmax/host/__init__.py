# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import logging
from ftrack_framework_core.host import Host
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
        'asset_manager': host_engine.MaxAssetManagerEngine,
        'loader': host_engine.MaxLoaderEngine,
        'opener': host_engine.MaxOpenerEngine,
        'publisher': host_engine.MaxPublisherEngine,
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
