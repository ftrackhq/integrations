# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os

from ftrack_framework_plugin import BasePlugin


class FileExistsValidatorPlugin(BasePlugin):
    name = 'file_exists_validator'

    def validate(self, file_path):
        '''
        Return True if given *file_path* exists, False If not.
        '''
        if not os.path.exists(file_path):
            return False
        return True

    def run(self, store):
        '''
        Expects collected_file in the <component_name> key of the given *store*.
        '''
        component_name = self.options.get('component')
        collected_file = store[component_name]['collected_file']

        if component_name:
            store[component_name]['valid_file'] = self.validate(collected_file)
        else:
            store['valid_file'] = self.validate(collected_file)
