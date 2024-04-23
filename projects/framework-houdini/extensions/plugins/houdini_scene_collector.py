# :coding: utf-8
# :copyright: Copyright (c) 2014-2024 ftrack

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class HoudiniSceneCollectorPlugin(BasePlugin):
    name = 'houdini_scene_collector'

    def run(self, store):
        '''
        Set the desired export_type for the current scene and the desired
        extension format to be published to the *store*. Also collect the
        scene_name and collect if scene is saved.
        '''
        try:
            self.logger.debug('TODO: Get scene name')
            scene_name = "TODO: scene_name"
            # TODO: get scene name from DCC
        except Exception as error:
            raise PluginExecutionError(
                f"Error retrieving the scene name: {error}"
            )
        try:
            self.logger.debug('TODO: check if DCC scene is saved')
            scene_saved = True
            # TODO: check if DCC scene is saved
        except Exception as error:
            raise PluginExecutionError(
                f"Error Checking if the scene is saved: {error}"
            )

        self.logger.debug(f"Current scene name is: {scene_name}.")

        component_name = self.options.get('component', 'main')

        store['components'][component_name]['scene_name'] = scene_name
        store['components'][component_name]['scene_saved'] = scene_saved
