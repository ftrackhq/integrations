# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import bpy
from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class BlenderSceneOpenerPlugin(BasePlugin):
    name = 'blender_scene_opener'

    def run(self, store):
        '''
        Calls the maya open function with the collected_path key stored in the given *store*
        '''
        component_name = self.options.get('component')

        collected_path = store['components'][component_name].get(
            'collected_path'
        )

        if not collected_path:
            raise PluginExecutionError("No path provided to open!")

        try:
            bpy.ops.wm.open_mainfile(filepath=collected_path)
        except Exception as error:
            raise PluginExecutionError(
                f"Couldn't open the given path. Error: {error}"
            )

        self.logger.debug(f"Blender scene opened. Path: {collected_path}")

        store['components'][component_name]['open_result'] = collected_path
