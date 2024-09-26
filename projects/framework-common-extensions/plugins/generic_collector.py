# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class GenericCollectorPlugin(BasePlugin):
    name = 'generic_collector'

    def run(self, store):
        '''
        Get folder_path and file_name from the :obj:`self.options`
        and store the collected_file in the given *store*.
        '''
        components = self.options.get('components', {})
        for component_name, component_value in components.items():
            file_path = component_value.get('file_path')
            if not file_path:
                message = (
                    "Please provide file_path in component options. \n "
                    "options: {}".format(self.options)
                )
                raise PluginExecutionError(message)
            self.logger.debug(f"Collected file_path: {file_path}.")
            if store.get('components') is None:
                store['components'] = {}
            if store['components'].get(component_name) is None:
                store['components'][component_name] = {}
            store['components'][component_name]['collected_path'] = file_path
