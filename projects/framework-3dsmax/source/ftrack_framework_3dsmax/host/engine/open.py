# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_framework_core.host.engine import OpenerEngine


class MaxOpenerEngine(OpenerEngine):
    engine_type = 'opener'

    def __init__(self, event_manager, host_types, host_id, asset_type_name):
        '''Initialise LoaderEngine with *event_manager*, *host*, *hostid* and
        *asset_type_name*'''
        super(MaxOpenerEngine, self).__init__(
            event_manager, host_types, host_id, asset_type_name
        )
