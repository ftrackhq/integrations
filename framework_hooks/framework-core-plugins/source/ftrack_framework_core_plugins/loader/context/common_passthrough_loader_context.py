# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants


class CommonPassthroughLoaderContextPlugin(BasePlugin):
    name = 'common_passthrough_loader_context'
    host_type = constants.host.PYTHON_HOST_TYPE
    plugin_type = constants.plugin.PLUGIN_CONTEXT_TYPE
    '''Option passthrough loader context plugin'''

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
        '''Merge context output with *options*'''
        output = self.methods['run'].get('required_output_value')
        output.update(options)
        return output

