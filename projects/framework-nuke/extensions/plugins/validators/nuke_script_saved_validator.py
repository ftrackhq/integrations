# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import nuke

from ftrack_framework_core.plugin import BasePlugin

from ftrack_framework_core.exceptions.plugin import (
    PluginExecutionError,
    PluginValidationError,
)

from ftrack_framework_nuke.utils import save_temp


class NukeScriptSavedValidatorPlugin(BasePlugin):
    '''Validate current Nuke script save status for publish'''

    name = 'nuke_script_saved_validator'

    def save_to_temp(self, store, extension_format):
        '''
        Save the Nuke script to a temporary location.
        '''
        try:
            save_path = save_temp()
        except Exception as error:
            raise PluginExecutionError(message=error)

        component_name = self.options.get('component', 'main')
        store['components'][component_name]['script_name'] = save_path
        self.logger.debug(f'Saved Nuke script to: {save_path}')
        store['components'][component_name]['script_saved'] = True

    def save_script(self, store):
        '''
        Save the current Maya scene.
        '''
        try:
            nuke.scriptSave()
        except Exception as error:
            raise PluginExecutionError(
                message=f"Error saving the scene: {error}"
            )

        component_name = self.options.get('component', 'main')
        store['components'][component_name]['script_saved'] = True
        self.logger.debug(f'Saved Nuke')

    def run(self, store):
        '''
        Validates if the current Nuke script is saved, based on the collected
         information at <component_name> key of the given *store*.
        '''
        component_name = self.options.get('component')
        script_name = store['components'][component_name]['script_name']
        script_saved = store['components'][component_name]['script_saved']

        if script_name == 'Root':
            # script is not saved, save it first.
            self.logger.warning('Nuke script not saved.')
            raise PluginValidationError(
                message='Nuke script is not saved, Click fix to save it to a temp file',
                on_fix_callback=self.save_to_temp,
            )
        elif not script_saved:
            self.logger.warning('Nuke script not saved')
            raise PluginValidationError(
                message='Nuke scene not saved, Click fix to save it.',
                on_fix_callback=self.save_script,
            )
