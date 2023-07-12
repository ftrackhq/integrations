# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_core import constants as core_constants
from ftrack_framework_core.host.engine import ResolverEngine


class UnrealResolverEngine(ResolverEngine):
    engine_type = core_constants.RESOLVER

    def __init__(
        self, event_manager, host_types, host_id, asset_type_name=None
    ):
        '''Initialise ResolverEngine with *event_manager*, *host*, *hostid*
        and *asset_type_name*'''
        super(UnrealResolverEngine, self).__init__(
            event_manager, host_types, host_id, asset_type_name
        )
