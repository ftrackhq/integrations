# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os

from ftrack_framework_plugin import BasePlugin
from ftrack_framework_plugin import constants


class CommonFileExistsPublisherValidatorPlugin(BasePlugin):
    '''Standalone publisher file validator plugin'''

    plugin_name = 'common_file_exists_publisher_validator'
    host_type = constants.hosts.PYTHON_HOST_TYPE
    plugin_type = constants.PLUGIN_VALIDATOR_TYPE

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=bool,
            required_output_value=True
        )

    def run(self, context_data=None, data=None, options=None):
        '''Validate if the file paths provided in *data* exists'''
        output = False
        all_files = []
        for plugin_dict in data:
            plugin_result = plugin_dict.get('result')
            all_files.extend(plugin_result)

        if len(all_files) != 0:
            output = True
            for datum in all_files:
                if not os.path.exists(datum):
                    output = False
                    self.logger.error("File {} does not exist".format(datum))

        return output
