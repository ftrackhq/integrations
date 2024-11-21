# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import bpy

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class BlenderSceneCollectorPlugin(BasePlugin):
    name = 'blender_scene_collector'

    def run(self, store):
        '''
        Set the desired export_type for the current blender scene and the desired
        extension format to be published to the *store*. Also collect the blender
        scene_name and collect if scene is saved.
        '''
        try:
            export_type = self.options['export_type']
        except Exception as error:
            raise PluginExecutionError(f"Provide export_type: {error}")
        try:
            scene_name= bpy.context.blend_data.filepath
        except Exception as error:
            raise PluginExecutionError(
                f"Error retrieving the scene name: {error}"
            )
        try:
            scene_saved = not bpy.data.is_dirty
        except Exception as error:
            raise PluginExecutionError(
                f"Error Checking if the scene is saved: {error}"
            )

        self.logger.debug(f"Export type set to {export_type}.")
        self.logger.debug(f"Current scene name is: {scene_name}.")
        self.logger.debug(f"Is current scene saved?: {scene_saved}.")

        component_name = self.options.get('component', 'main')
        store['components'][component_name]['export_type'] = export_type

        store['components'][component_name]['scene_name'] = scene_name
        store['components'][component_name]['scene_saved'] = scene_saved
