# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import nuke

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class NukeNodeCollectorPlugin(BasePlugin):
    name = 'nuke_node_collector'

    def ui_hook(self, payload):
        '''
        Return all available nodes in the current nuke script.
        '''
        node_names = []
        for node in nuke.allNodes():
            node_names.append(node.name())
        selected_nodes = nuke.selectedNodes()
        if len(selected_nodes) > 0:
            selected_node = selected_nodes[0].name()
            # Remove and add the selected node to the top of the list, so
            # user still can select among all nodes
            node_names.remove(selected_node)
            node_names.insert(0, selected_node)
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
