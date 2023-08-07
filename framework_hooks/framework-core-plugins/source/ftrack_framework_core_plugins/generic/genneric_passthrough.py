# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_plugin import BasePlugin
from ftrack_framework_plugin import constants

# TODO: double check we are allowed to do this, or we should not use constants
#  here, or have host available in base plugin to be able to do something
#  like: host.constants.stage_types.COLLECTOR
from ftrack_framework_core import constants as core_constants

class GenericPassthroughPlugin(BasePlugin):
    name = 'generic_passthrough'
    host_type = constants.hosts.PYTHON_HOST_TYPE
    plugin_type = constants.PLUGIN_GENERIC_TYPE
    '''Empty/passthrough loader finalizer plugin'''

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=dict,
            required_output_value=None
        )

    def run(self, context_data=None, data=None, options=None):
        # Example of getting the previous collector data from plugin_data
        self.get_previous_stage_data(
            plugin_data=data,
            stage_name=core_constants.COLLECTOR
        )
        return {}
