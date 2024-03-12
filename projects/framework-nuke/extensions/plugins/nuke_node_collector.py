# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import nuke

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class NukeWritenodeCollectorPlugin(BasePlugin):
    name = 'nuke_node_collector'

    def ui_hook(self, payload):
        '''
        Return all available write nodes in Nuke
        '''
        selected_nodes = nuke.selectedNodes()
        if len(selected_nodes) == 0:
            selected_nodes = nuke.allNodes()
        node_names = []
        for node in selected_nodes:
            if node.Class().startswith("write"):
                node_names.append(node.name())
        return node_names

    def run(self, store):
        '''
        Set the selected writenode name to the *store*
        '''
        try:
            node_name = self.options['node_name']
        except Exception as error:
            raise PluginExecutionError(f"Provide node_name: {error}")

        self.logger.debug(f"Nnode {node_name}, has been collected.")
        component_name = self.options.get('component', 'main')
        store['components'][component_name]['node_name'] = node_name
