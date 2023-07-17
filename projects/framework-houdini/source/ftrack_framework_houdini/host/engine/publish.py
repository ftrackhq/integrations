# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

from ftrack_framework_core import constants as core_constants
from ftrack_framework_core.host.engine import PublisherEngine


class HoudiniPublisherEngine(PublisherEngine):
    engine_type = core_constants.PUBLISHER

    def __init__(self, event_manager, host_types, host_id, asset_type_name):
        '''Initialise publisherEngine with *event_manager*, *host*, *hostid* and
        *asset_type_name*'''
        super(HoudiniPublisherEngine, self).__init__(
            event_manager, host_types, host_id, asset_type_name
        )
