# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants

class GenericPassthroughPlugin(BasePlugin):
    name = 'generic_passthrough'
    host_type = constants.host.PYTHON_HOST_TYPE
    plugin_type = constants.plugin.PLUGIN_GENERIC_TYPE
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
            stage_name=constants.definition.COLLECTOR
        )
        return {}
