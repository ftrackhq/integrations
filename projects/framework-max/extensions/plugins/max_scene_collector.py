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
        scene_name = None
        scene_saved = False
        try:
            scene_name = os.path.join(rt.maxFilePath, rt.maxFileName)
        except Exception as error:
            raise PluginExecutionError(
                f"Error retrieving the scene name: {error}"
            )
        try:
            scene_saved = not rt.getSaveRequired()
        except Exception as error:
            raise PluginExecutionError(
                f"Error Checking if the scene is saved: {error}"
            )

        self.logger.debug(f"Current scene name is: {scene_name}.")

        component_name = self.options.get('component', 'main')

        store['components'][component_name]['scene_name'] = scene_name
        store['components'][component_name]['scene_saved'] = scene_saved
