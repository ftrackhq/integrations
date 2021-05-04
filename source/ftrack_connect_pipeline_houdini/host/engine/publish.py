# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

from ftrack_connect_pipeline.host.engine import PublisherEngine


class HoudiniPublisherEngine(PublisherEngine):
    engine_type = 'publisher'

    def __init__(self, event_manager, host_types, host_id, asset_type):
        '''Initialise publisherEngine with *event_manager*, *host*, *hostid* and
        *asset_type*'''
        super(HoudiniPublisherEngine, self).__init__(event_manager, host_types,
                                                     host_id, asset_type)



