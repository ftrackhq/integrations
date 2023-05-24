# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

import logging

from ftrack_framework_qt import constants as qt_constants
from ftrack_framework_houdini import constants as houdini_constants
from ftrack_framework_core.host import Host
from ftrack_framework_houdini.host import engine as host_engine


logger = logging.getLogger(__name__)


class HoudiniHost(Host):
    host_types = [qt_constants.HOST_TYPE, houdini_constants.HOST_TYPE]

    # Define the Houdini engines to be run during the run function
    engines = {
        'asset_manager': host_engine.HoudiniAssetManagerEngine,
        'opener': host_engine.HoudiniOpenerEngine,
        'loader': host_engine.HoudiniLoaderEngine,
        'publisher': host_engine.HoudiniPublisherEngine,
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
