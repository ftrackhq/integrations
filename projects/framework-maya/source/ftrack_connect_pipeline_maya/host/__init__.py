# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import logging
from framework_core.host import Host
from framework_qt import constants as qt_constants
from framework_maya import constants as maya_constants
from framework_maya.host import engine as host_engine

logger = logging.getLogger(__name__)


class MayaHost(Host):
    '''
    MayaHost class.
    '''

    host_types = [qt_constants.HOST_TYPE, maya_constants.HOST_TYPE]
    # Define the Maya engines to be run during the run function
    engines = {
        'asset_manager': host_engine.MayaAssetManagerEngine,
        'loader': host_engine.MayaLoaderEngine,
        'opener': host_engine.MayaOpenerEngine,
        'publisher': host_engine.MayaPublisherEngine,
    }

    def __init__(self, event_manager):
        '''
        Initialize MayaHost with *event_manager*.

        *event_manager* instance of
        :class:`framework_core.event.EventManager`
        '''
        super(MayaHost, self).__init__(event_manager)

    def run(self, event):
        runnerResult = super(MayaHost, self).run(event)
        return runnerResult
