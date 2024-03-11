# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import maya.cmds as cmds

from ftrack_utils.paths import get_temp_path
from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class MayaSaveToTempPlugin(BasePlugin):
    name = 'maya_save_to_temp_finalizer'

    def run(self, store):
        '''
        Makes sure that the current opened scene is saved to a temporary file so
        prevents it to be overridden.
        '''

        scene_type = cmds.file(query=True, type=True)
        if not scene_type:
            raise PluginExecutionError(
                "Can't query the scene type of the current opened scene"
            )
        if scene_type[0] == 'mayaBinary':
            scene_type = 'mb'
        elif scene_type[0] == 'mayaAscii':
            scene_type = 'ma'
        else:
            raise PluginExecutionError(
                f" Scene type {scene_type}, not supported"
            )

        try:
            # Save file to a temp file
            save_path = get_temp_path(filename_extension=scene_type)
            # Save Maya scene to this path
            cmds.file(rename=save_path)
            cmds.file(save=True)
            self.logger.debug(f"Maya scene saved to temp path: {save_path}")
        except Exception as error:
            raise PluginExecutionError(
                message=f"Error attempting to save the current scene to a "
                f"temporal path: {error}"
            )
