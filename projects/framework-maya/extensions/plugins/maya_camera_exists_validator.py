# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import maya.cmds as cmds

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginValidationError


class MayaCameraExistsValidatorPlugin(BasePlugin):
    '''
    Plugin to validate if a camera exists.
    '''

    name = 'maya_camera_exists_validator'

    def run(self, store):
        '''
        Run the validation process.
        '''
        component_name = self.options.get('component', 'main')
        camera_name = store['components'][component_name].get('camera_name')
        if not cmds.objExists(camera_name):
            raise PluginValidationError(
                message=f"Camera with name {camera_name} doesn't exists"
            )
        self.logger.debug(f"Camera {camera_name} exists.")
        store['components'][component_name]['valid_camera'] = True
