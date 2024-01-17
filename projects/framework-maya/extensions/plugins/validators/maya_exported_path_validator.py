# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginValidationError


class MayaExportedPathValidatorPlugin(BasePlugin):
    '''
    Plugin to validate if a camera exists.
    '''

    name = 'maya_exported_path_validator'

    def run(self, store):
        '''
        Run the validation process.
        '''
        component_name = self.options.get('component', 'main')
        exported_path = store['components'][component_name].get(
            'exported_path'
        )
        if not os.path.exists(exported_path):
            raise PluginValidationError(
                message=f"The file {exported_path} doesn't exists"
            )
        store['components'][component_name]['successful_export'] = True
