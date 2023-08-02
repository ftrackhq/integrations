# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_plugin import BasePlugin
from ftrack_framework_plugin import constants

class GenericContextPassthroughPlugin(BasePlugin):
    plugin_name = 'generic_context_passthrough'
    host_type = constants.hosts.PYTHON_HOST_TYPE
    plugin_type = constants.PLUGIN_CONTEXT_TYPE
    '''Return the given options'''

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=dict,
            required_output_value={
                'context_id': None,
                'asset_name': None,
                'comment': None,
                'status_id': None,
            }
        )

    def run(self, context_data=None, data=None, options=None):
        self.logger.debug("given options: {}".format(options))
        required_output = self.methods.get('run').required_output_value
        self.logger.debug("required_output: {}".format(required_output))
        return required_output.update(options)
