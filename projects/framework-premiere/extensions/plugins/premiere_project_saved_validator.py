# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import (
    PluginExecutionError,
    PluginValidationError,
)

from ftrack_utils.rpc import JavascriptRPC


class PremiereProjectSavedValidatorPlugin(BasePlugin):
    '''
    Plugin to validate if the Premiere project has been saved.
    '''

    name = 'premiere_project_saved_validator'

    def run(self, store):
        '''
        Run the validation process for the Premiere project.
        '''
        component_name = self.options.get('component', 'main')

        # Premiere does not support checking if document is saved, so we will
        # save the document instead.
        # Note: Premiere cannot have unsaved projects - they always have a path.

        # Get existing RPC connection instance
        premiere_connection = JavascriptRPC.instance()

        save_result = premiere_connection.rpc('saveProject')
        # Will return a boolean containing the result.
        if not save_result or isinstance(save_result, str):
            raise PluginExecutionError(
                f'An error occurred while saving the'
                f' project: {save_result}'
            )
        elif save_result:
            self.logger.info('Project saved successfully.')

        self.logger.debug("Project is saved validation passed.")
        store['components'][component_name]['valid_file'] = True
