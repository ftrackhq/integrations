# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants


class FileExistsValidatorPlugin(BasePlugin):
    name = 'file_exists_validator'
    host_type = constants.host.PYTHON_HOST_TYPE
    plugin_type = constants.plugin.PLUGIN_VALIDATOR_TYPE
    '''Return the full path of the file passed in the options'''

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=bool,
            required_output_value=True,
        )
        self.register_method(
            method_name='validate',
            required_output_type=bool,
            required_output_value=True,
        )

    def validate(self, context_data=None, data=None, options=None):
        '''
        Expects a list of file paths in the given *data* dictionary in the
        collector_result key.
        '''
        collector_result = data['collector_result']
        if type(collector_result) == str:
            collector_result = [data['collector_result']]
        exists = True
        for result in collector_result:
            if not os.path.exists(result):
                exists = False
                break
        return exists

    def run(self, context_data=None, data=None, options=None):
        '''
        Expects previous collector result in the given *data*.
        Return the value of validate method.
        '''
        # Pick plugins from previous collector stage
        collector_plugins = []
        for key, value in data[self.plugin_step_name]['collector'].items():
            collector_plugins.append({key: value})
        # Pick result of collector plugins.
        collector_result = []
        for plugin in collector_plugins:
            collector_result.extend(list(plugin.values()))

        return self.validate(data={'collector_result': collector_result})
