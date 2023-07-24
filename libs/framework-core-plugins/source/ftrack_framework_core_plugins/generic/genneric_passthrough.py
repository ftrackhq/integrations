# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_plugin import BasePlugin
from ftrack_framework_plugin import constants

class GenericPassthroughPlugin(BasePlugin):
    plugin_name = 'generic_passthrough'
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
        return {}
