# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack


from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import (
    PluginExecutionError,
    PluginValidationError,
)

import hou


class HoudiniSceneSavedValidatorPlugin(BasePlugin):
    '''
    Plugin to validate if the scene has been saved.
    '''

    name = 'houdini_scene_saved_validator'

    def save_to_temp(self, store, extension_format):
        '''
        Save the file to a temporary location.
        '''
        try:
            # Save file to a temp file
            save_path = get_temp_path(filename_extension=extension_format)
            hou.hipFile.save(save_path, False)
            self.logger.debug(f"Scene has been saved to: {save_path}.")
        except Exception as error:
            raise PluginExecutionError(message=error)

        component_name = self.options.get('component', 'main')
        store['components'][component_name]['scene_name'] = save_path
        store['components'][component_name]['scene_saved'] = True
        store['components'][component_name]['valid_file'] = True

    def save_scene(self, store):
        '''
        Save the current scene.
        '''
        try:
            hou.hipFile.save(None, False)
            self.logger.debug(f"Scene has been saved.")
        except Exception as error:
            raise PluginExecutionError(
                message=f"Error saving the scene: {error}"
            )

        component_name = self.options.get('component', 'main')
        store['components'][component_name]['scene_saved'] = True
        store['components'][component_name]['valid_file'] = True

    def run(self, store):
        '''
        Run the validation process for the scene.
        '''
        component_name = self.options.get('component', 'main')

        scene_name = store['components'][component_name].get('scene_name')
        scene_saved = store['components'][component_name].get('scene_saved')

        if not scene_name:
            # Scene is not saved, save it first.
            self.logger.warning('Houdini scene has never been saved.')
            raise PluginValidationError(
                message='Houdini scene has never been saved, Click fix to save it to a temp file',
                on_fix_callback=self.save_to_temp,
                fix_kwargs={'extension_format': 'hip'},
            )
        if not scene_saved:
            self.logger.warning('Houdini scene not saved')
            raise PluginValidationError(
                message='Houdini scene not saved, Click fix to save it.',
                on_fix_callback=self.save_scene,
            )
        self.logger.debug("Scene is saved validation passed.")
        store['components'][component_name]['valid_file'] = True
