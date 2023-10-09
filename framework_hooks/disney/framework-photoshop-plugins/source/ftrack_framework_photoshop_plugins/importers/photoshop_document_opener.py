# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants


class PSDocumentOpenerPlugin(BasePlugin):
    name = 'photoshop_document_opener'
    host_type = constants.host.PYTHON_HOST_TYPE
    plugin_type = constants.plugin.PLUGIN_IMPORTER_TYPE
    '''Return the full path of the document passed in the options'''

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
        # TODO: to be implemented
        return ""
