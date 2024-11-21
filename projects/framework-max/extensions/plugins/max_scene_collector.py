# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

from pymxs import runtime as rt


class MaxSceneCollectorPlugin(BasePlugin):
    name = 'max_scene_collector'

    def run(self, store):
        '''
        Set the desired export_type for the current scene and the desired
        extension format to be published to the *store*. Also collect the
        scene_name and collect if scene is saved.
        '''
        export_type = None
        try:
            export_type = self.options['export_type']
        except Exception as error:
            raise PluginExecutionError(
                f"Provide export_type and extension_format: {error}"
            )

        scene_name = None
        try:
            scene_name = os.path.join(rt.maxFilePath, rt.maxFileName)
        except Exception as error:
            raise PluginExecutionError(
                f"Error retrieving the scene name: {error}"
            )

        scene_saved = False
        try:
            scene_saved = not rt.getSaveRequired()
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
