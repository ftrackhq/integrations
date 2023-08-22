# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging
from ftrack_framework_core.host import Host
from ftrack_framework_core import constants as core_constants
from ftrack_framework_qt import constants as qt_constants
from ftrack_framework_maya import constants as maya_constants
from ftrack_framework_maya.host import engine as host_engine

logger = logging.getLogger(__name__)


class MayaHost(Host):
    '''
    MayaHost class.
    '''

    host_types = [qt_constants.HOST_TYPE, maya_constants.HOST_TYPE]
    # Define the Maya engines to be run during the run function
    engines = {
        core_constants.PUBLISHER: host_engine.MayaPublisherEngine,
        core_constants.LOADER: host_engine.MayaLoaderEngine,
        core_constants.OPENER: host_engine.MayaOpenerEngine,
        core_constants.ASSET_MANAGER: host_engine.MayaAssetManagerEngine,
        core_constants.RESOLVER: host_engine.MayaResolverEngine,
    }

    def __init__(self, event_manager):
        '''
        Initialize MayaHost with *event_manager*.

        *event_manager* instance of
        :class:`ftrack_framework_core.event.EventManager`
        '''
        super(MayaHost, self).__init__(event_manager)

    def run(self, event):
        runnerResult = super(MayaHost, self).run(event)
        return runnerResult
