# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import bpy
from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginValidationError


class BlenderCameraExistsValidatorPlugin(BasePlugin):
    '''
    Plugin to validate if a camera exists.
    '''

    name = 'blender_camera_exists_validator'

    def run(self, store):
        '''
        Check camera exists.
        '''
        component_name = self.options.get('component', 'main')
        camera_name = store['components'][component_name].get('camera_name')
        if (
            not bpy.data.objects[camera_name]
            or bpy.data.objects[camera_name].type != 'CAMERA'
        ):
            raise PluginValidationError(
                message=f"Camera with name {camera_name} doesn't exists"
            )
        self.logger.debug(f"Camera {camera_name} exists.")
        store['components'][component_name]['valid_camera'] = True
