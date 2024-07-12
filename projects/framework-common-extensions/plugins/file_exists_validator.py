# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginValidationError

import clique


class FileExistsValidatorPlugin(BasePlugin):
    name = 'file_exists_validator'

    def validate(self, file_path):
        '''
        Return True if given *file_path* exists, False If not.
        '''
        if not os.path.exists(file_path):
            try:
                collection = clique.parse(file_path)
                for file_path in collection:
                    if not os.path.exists(file_path):
                        raise PluginValidationError(
                            message=f'File {file_path} does not exist.'
                        )
            except Exception as error:
                raise PluginValidationError(
                    message=f'File {file_path} does not exist, and is not a valid collection, error: {error}'
                )
        self.logger.debug(f"{file_path} Exists.")
        return True

    def run(self, store):
        '''
        Expects collected_path in the <component_name> key of the given *store*.
        '''
        component_name = self.options.get('component')
        collected_path = store['components'][component_name]['collected_path']

        store['components'][component_name]['valid_path'] = self.validate(
            collected_path
        )
