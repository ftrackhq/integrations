# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import bpy
from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class BlenderCameraCollectorPlugin(BasePlugin):
    name = 'blender_camera_collector'

    def ui_hook(self, payload):
        '''
        Return all available cameras in Blender
        '''
        cameras_obj = [cam.name for cam in bpy.data.objects if cam.type == 'CAMERA']
        return cameras_obj

    def run(self, store):
        '''
        Set the selected camera name to the *store*
        '''

        try:
            camera_name = self.options['camera_name']
        except Exception as error:
            raise PluginExecutionError(f"Provide camera_name: {error}")

        self.logger.debug(f"Camera {camera_name}, has been collected.")
        component_name = self.options.get('component', 'main')
        store['components'][component_name]['camera_name'] = camera_name