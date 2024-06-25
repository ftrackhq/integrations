# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import hou

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class HoudiniSceneLoaderPlugin(BasePlugin):
    name = 'houdini_scene_loader'

    def run(self, store):
        '''
        Set the selected camera name to the *store*
        '''

        component_path = store.get('component_path')
        if not component_path:
            raise PluginExecutionError(f'No component path provided in store!')

        try:
            node = hou.node('/obj').createNode(
                'subnet', context_data['asset_name']
            )
            node.loadItemsFromFile(component_path.replace('\\', '/'))
            node.setSelected(True)
            node.moveToGoodPosition()
        except RuntimeError as error:
            raise PluginExecutionError(
                f"Failed to import {component_path} to scene. Error: {error}"
            )
        self.logger.debug(
            f"Component {component_path} has been loaded to scene."
        )
