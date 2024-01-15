# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os

from ftrack_framework_core.plugin import BasePlugin


class ScriptValidatorPlugin(BasePlugin):
    name = 'script_validator'

    def validate(self, collected_script):
        '''
        Return True if current Nuke script and/or path given in *collected_script*
        is valid for publish, Raise an PluginValidationError otherwise.
        '''
        return True

    def run(self, store):
        '''
        Expects collected_data in the <component_name> key of the given *store*.
        '''
        component_name = self.options.get('component')
        collected_script = store['components'][component_name][
            'collected_script'
        ]

        store['components'][component_name]['valid_script'] = self.validate(
            collected_script
        )
