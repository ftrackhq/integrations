# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants


class FileCollectorPlugin(BasePlugin):
    name = 'file_collector'
    host_type = constants.host.PYTHON_HOST_TYPE
    plugin_type = constants.plugin.PLUGIN_COLLECTOR_TYPE
    '''Return the full path of the file passed in the options'''

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=str,
            required_output_value=None,
        )

    def run(self, context_data=None, data=None, options=None):
        '''
        Get folder_path and file_name from the given *options* and return the
        join full path.
        '''
        folder_path = options.get('folder_path')
        file_name = options.get('file_name')
        if not folder_path or not file_name:
            self.status = constants.status.ERROR_STATUS
            self.message = (
                "Please provide folder_path and file_name in options. \n "
                "options: {}".format(options)
            )
            return ''

        return os.path.join(folder_path, file_name)
