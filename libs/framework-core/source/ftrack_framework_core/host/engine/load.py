# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_framework_core import constants
from ftrack_framework_core.host.engine import BaseEngine


class LoaderEngine(BaseEngine):
    engine_type = constants.LOADER

    def __init__(self, event_manager, host_types, host_id, asset_type_name):
        super(LoaderEngine, self).__init__(
            event_manager, host_types, host_id, asset_type_name
        )
