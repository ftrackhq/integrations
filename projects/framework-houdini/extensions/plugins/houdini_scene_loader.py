# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import hou

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class HoudiniSceneLoaderPlugin(BasePlugin):
    name = 'houdini_scene_loader'

    def run(self, store):
        '''
        Load a Houdini scene from component path provided in *store*. Saves the
        loaded node name to the store.
        '''

        component_path = store.get('component_path')
        if not component_path:
            raise PluginExecutionError(f'No component path provided in store!')

        component = self.session.query(
            f"Component where id={store['entity_id']}"
        ).first()

        try:
            node = hou.node('/obj').createNode(
                'subnet', component['version']['asset']['name']
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
        store['loaded_node'] = node.path()
