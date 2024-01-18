# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os

from ftrack_framework_core.plugin import BasePlugin


class NukeScriptValidatorPlugin(BasePlugin):
    '''Validate current Nuke script for publish'''

    name = 'nuke_script_validator'

    def validate(self, collected_script):
        '''
        Return True if current Nuke script and/or path given in *collected_script*
        is valid for publish, Raise an PluginValidationError otherwise.
        '''
        return True

    def run(self, store):
        '''
        Validates the Nuke script before publish.
        '''
        component_name = self.options.get('component')
        script_name = store['components'][component_name]['script_name']

        self.logger.debug(f'Validating: {script_name}')
        store['components'][component_name]['valid_script'] = self.validate(
            script_name
        )
