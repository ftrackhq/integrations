# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline.host.definition import DefintionManager
from ftrack_connect_pipeline.host.runner import Runner

import logging

logger = logging.getLogger(__name__)


class Host(object):
    def __init__(self, event_manager, host):
        self._definition_manager = DefintionManager(event_manager, host)
        print self._definition_manager.json_definitions
        self._runner = Runner(
            event_manager,
            self._definition_manager.json_definitions,
            host,
            self._definition_manager.definitions.hostid
)