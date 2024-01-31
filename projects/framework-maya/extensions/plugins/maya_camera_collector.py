# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import maya.cmds as cmds

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class MayaCameraCollectorPlugin(BasePlugin):
    name = 'maya_camera_collector'

    def ui_hook(self, payload):
        '''
        Return all available cameras in Maya
        '''
        collected_objects = cmds.listCameras()
        return collected_objects

    def run(self, store):
        '''
        Set the desired export_type for the current maya scene and the desired
        extension format to be publisher to the store.
        '''
        try:
            camera_name = self.options['camera_name']
        except Exception as error:
            raise PluginExecutionError(f"Provide camera_name: {error}")

        self.logger.debug(f"Camera {camera_name}, has been collected.")
        component_name = self.options.get('component', 'main')
        store['components'][component_name]['camera_name'] = camera_name
