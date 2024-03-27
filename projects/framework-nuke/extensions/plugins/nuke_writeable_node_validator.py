# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import nuke

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginValidationError


class NukeWriteableNodeValidatorPlugin(BasePlugin):
    '''
    Plugin to validate if a nuke node exists.
    '''

    name = 'nuke_writeable_node_validator'

    def clean_selection(self):
        '''Clean the current selection in Nuke.'''
        for node in nuke.selectedNodes():
            node['selected'].setValue(False)

    def run(self, store):
        '''
        Check node exists.
        '''
        component_name = self.options.get('component', 'main')
        node_name = store['components'][component_name].get('node_name')

        node = nuke.toNode(node_name)
        selected_nodes = nuke.selectedNodes()
        self.clean_selection()

        write_node = nuke.createNode('Write')
        try:
            if not write_node.setInput(0, node):
                raise PluginValidationError(
                    "The selected node can't be connected"
                    f" to a write node: {node_name}"
                )
        finally:
            # delete temporary write node
            nuke.delete(write_node)

            # restore selection
            self.clean_selection()
            for node in selected_nodes:
                node['selected'].setValue(True)

        self.logger.debug(f'Node "{node_name}" exists.')
        store['components'][component_name]['valid_node'] = True
