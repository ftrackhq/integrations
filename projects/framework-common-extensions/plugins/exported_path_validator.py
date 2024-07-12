# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os

import clique

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginValidationError


class ExportedPathsValidatorPlugin(BasePlugin):
    '''
    Plugin to validate if exported_paths of all components in the store exists.
    '''

    name = 'exported_paths_validator'

    def run(self, store):
        '''
        Run the validation process.
        '''
        for component_name in list(store['components'].keys()):
            exported_path = store['components'][component_name].get(
                'exported_path'
            )
            if not exported_path:
                continue
            if not os.path.exists(exported_path):
                try:
                    collection = clique.parse(exported_path)
                    for file_path in collection:
                        if not os.path.exists(file_path):
                            raise PluginValidationError(
                                message=f'File {file_path} does not exist.'
                            )
                except Exception as error:
                    raise PluginValidationError(
                        message=f'File {exported_path} does not exist, and is not a valid collection, error: {error}'
                    )
            self.logger.debug(f"Exported path {exported_path} exists.")
