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
            # Check if image sequence
            dirname, basename = os.path.split(exported_path)
            if basename.find("%d") > -1:
                collection = clique.parse(exported_path)
                if not collection:
                    raise PluginValidationError(
                        message=f"Could not parse image sequence from: {exported_path}"
                    )
            else:
                if not os.path.exists(exported_path):
                    raise PluginValidationError(
                        message=f"The file {exported_path} doesn't exists"
                    )
                self.logger.debug(f"Exported path {exported_path} exists.")
