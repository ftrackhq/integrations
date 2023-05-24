# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import logging
import ftrack_api
from ftrack_framework_qt import constants as qt_constants
from ftrack_framework_nuke import constants as nuke_constants
from ftrack_framework_core.host import Host
from ftrack_framework_nuke.host import engine as host_engine


logger = logging.getLogger(__name__)


class NukeHost(Host):
    host_types = [qt_constants.HOST_TYPE, nuke_constants.HOST_TYPE]
    # Define the Nuke engines to be run during the run function
    engines = {
        'asset_manager': host_engine.NukeAssetManagerEngine,
        'loader': host_engine.NukeLoaderEngine,
        'opener': host_engine.NukeOpenerEngine,
        'publisher': host_engine.NukePublisherEngine,
    }

    def __init__(self, event_manager):
        '''
        Initialize NukeHost with *event_manager*.

        *event_manager* instance of
        :class:`ftrack_framework_core.event.EventManager`
        '''
        super(NukeHost, self).__init__(event_manager)

    def run(self, event):
        runnerResult = super(NukeHost, self).run(event)
        return runnerResult
