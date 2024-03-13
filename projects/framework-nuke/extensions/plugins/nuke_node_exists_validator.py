# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import nuke

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginValidationError


class NukeNodeExistsValidatorPlugin(BasePlugin):
    '''
    Plugin to validate if a nuke node exists.
    '''

    name = 'nuke_node_exists_validator'

    def run(self, store):
        '''
        Check node exists.
        '''
        component_name = self.options.get('component', 'main')
        node_name = store['components'][component_name].get('node_name')
        if not nuke.toNode(node_name):
            raise PluginValidationError(
                message=f'Nuke node with name "{node_name}" does not exist'
            )
        self.logger.debug(f'Node "{node_name}" exists.')
        store['components'][component_name]['valid_node'] = True
