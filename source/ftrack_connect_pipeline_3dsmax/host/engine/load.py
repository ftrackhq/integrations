# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline.host.engine import LoaderEngine


class MaxLoaderEngine(LoaderEngine):
    engine_type = 'loader'

    def __init__(self, event_manager, host_types, host_id, asset_type):
        '''Initialise LoaderEngine with *event_manager*, *host*, *hostid* and
        *asset_type*'''
        super(MaxLoaderEngine, self).__init__(event_manager, host_types, host_id,
                                           asset_type)



