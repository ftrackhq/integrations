# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline.host.engine import OpenerEngine


class NukeOpenerEngine(OpenerEngine):
    engine_type = 'opener'

    def __init__(self, event_manager, host_types, host_id, asset_type_name):
        '''Initialise OpenerEngine with *event_manager*, *host*, *hostid* and
        *asset_type_name*'''
        super(NukeOpenerEngine, self).__init__(
            event_manager, host_types, host_id, asset_type_name
        )
