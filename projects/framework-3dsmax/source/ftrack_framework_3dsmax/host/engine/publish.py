# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_framework_core.host.engine import PublisherEngine


class MaxPublisherEngine(PublisherEngine):
    engine_type = 'publisher'

    def __init__(self, event_manager, host_types, host_id, asset_type_name):
        '''Initialise publisherEngine with *event_manager*, *host*, *hostid* and
        *asset_type_name*'''
        super(MaxPublisherEngine, self).__init__(
            event_manager, host_types, host_id, asset_type_name
        )
