# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os

from ftrack_framework_plugin import BasePlugin


class DocumentValidatorPlugin(BasePlugin):
    name = 'document_validator'

    def validate(self, collected_data):
        '''
        Return True if given *collected_data* is valid for publish, False If not.
        '''
        return True

    def run(self, store):
        '''
        Expects collected_data in the <component_name> key of the given *store*.
        '''
        component_name = self.options.get('component')
        collected_file = store['components'][component_name]['collected_data']

        store['components'][component_name]['valid_document'] = self.validate(
            collected_file
        )
