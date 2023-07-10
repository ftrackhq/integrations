# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_core.host.engine import BaseEngine


class ResolverEngine(BaseEngine):
    engine_type = 'resolver'

    def __init__(self, event_manager, host_types, host_id, asset_type_name):
        super(ResolverEngine, self).__init__(
            event_manager, host_types, host_id, asset_type_name
        )
