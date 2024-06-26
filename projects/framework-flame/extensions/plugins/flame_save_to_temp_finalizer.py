# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_utils.paths import get_temp_path
from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class FlameSaveToTempPlugin(BasePlugin):
    name = 'flame_save_to_temp_finalizer'

    def run(self, store):
        '''
        Makes sure that the current opened scene is saved to a temp file so
        prevents it to be overriden.
        '''
        scene_type = '.mb'

        try:
            # Save file to a temp file
            save_path = get_temp_path(filename_extension=scene_type)
            # Save Flame scene to this path

            self.logger.debug(
                f"Flame scene saved to temp path: {save_path}"
            )
        except Exception as error:
            raise PluginExecutionError(
                message=f"Error attempting to save the current scene to a "
                f"temporal path: {error}"
            )
