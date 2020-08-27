# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline.host.engine import PublisherEngine


class NukePublisherEngine(PublisherEngine):
    engine_type = 'publisher'

    def __init__(self, event_manager, host, hostid, asset_type):
        '''Initialise publisherEngine with *event_manager*, *host*, *hostid* and
        *asset_type*'''
        super(NukePublisherEngine, self).__init__(event_manager, host, hostid,
                                              asset_type)



