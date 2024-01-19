# :coding: utf-8
# :copyright: Copyright (c) 2014-2024 ftrack

import nuke

from ftrack_framework_core.plugin import BasePlugin

from ftrack_framework_core.exceptions.plugin import (
    PluginExecutionError,
    PluginValidationError,
)

from ftrack_utils.paths import get_temp_path


class NukeScriptSavedValidatorPlugin(BasePlugin):
    '''Validate current Nuke script save status for publish'''

    name = 'nuke_script_saved_validator'

    def save_to_temp(self, store):
        '''
        Save the Nuke script to a temporary location, and update the path in the
        *store*.
        '''
        try:
            save_path = get_temp_path(filename_extension='.nk')

            nuke.scriptSaveAs(save_path, overwrite=1)
        except Exception as error:
            raise PluginExecutionError(message=error)

        component_name = self.options.get('component', 'main')
        store['components'][component_name]['script_name'] = save_path
        self.logger.debug(f'Saved Nuke script to: {save_path}')
        store['components'][component_name]['script_saved'] = True

    def save_script(self, store):
        '''
        Save the current Maya scene, and update the *store*.
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
            raise PluginValidationError(
                message='Nuke script has never been saved, applying fix to save it to a temp file',
                on_fix_callback=self.save_to_temp,
            )
        elif not script_saved:
            raise PluginValidationError(
                message='Nuke script not saved, applying fix to save it.',
                on_fix_callback=self.save_script,
            )
