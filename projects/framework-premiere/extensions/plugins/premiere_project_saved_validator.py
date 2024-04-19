# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os

from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import (
    PluginExecutionError,
    PluginValidationError,
)

from ftrack_utils.rpc import JavascriptRPC


class PremiereDocumentSavedValidatorPlugin(BasePlugin):
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
            self.logger.info(
                'Project saved successfully, fetch the path again'
            )

        try:
            project_name = premiere_connection.rpc('getProjectPath')
        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(
                f'Exception querying the project data: {e}'
            )

        if project_name != store['components'][component_name].get(
            'project_name'
        ):
            self.logger.warning('Project name has changed, updating the store')
            store['components'][component_name]['project_name'] = project_name

        self.logger.debug("Project is saved validation passed.")
        store['components'][component_name]['valid_file'] = True
