# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants


class GenericPassthroughPlugin(BasePlugin):
    name = 'generic_passthrough'
    host_type = constants.host.PYTHON_HOST_TYPE
    plugin_type = constants.plugin.PLUGIN_GENERIC_TYPE
    '''Empty/passthrough loader finalizer plugin'''

    # TODO: we should not have passthrough plugins. Instead if a plugin is not
    #  defined in a tool_config, just go to the next step.
    #  (There should be a task to implement this.)
    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=dict,
            required_output_value=None,
        )

    def run(self, context_data=None, data=None, options=None):
        return {}
