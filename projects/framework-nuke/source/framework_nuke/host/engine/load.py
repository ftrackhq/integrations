# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from framework_core.host.engine import LoaderEngine


class NukeLoaderEngine(LoaderEngine):
    engine_type = 'loader'

    def __init__(self, event_manager, host_types, host_id, asset_type_name):
        '''Initialise LoaderEngine with *event_manager*, *host*, *hostid* and
        *asset_type_name*'''
        super(NukeLoaderEngine, self).__init__(
            event_manager, host_types, host_id, asset_type_name
        )
