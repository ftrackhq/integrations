# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline.host.engine import LoaderEngine


class MayaLoaderEngine(LoaderEngine):
    engine_type = 'loader'

    def __init__(self, event_manager, host, hostid, asset_type):
        '''Initialise LoaderEngine with *event_manager*, *host*, *hostid* and
        *asset_type*'''
        super(MayaLoaderEngine, self).__init__(event_manager, host, hostid,
                                           asset_type)



