# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os
import re

from ftrack_utils.paths import check_image_sequence
from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginValidationError


class ExportedPathsValidatorPlugin(BasePlugin):
    '''
    Plugin to validate if exported_paths of all components in the store exists.

    Expected format: folder/image.%d.jpg [1-35]
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
            # Check if image sequence - having "%d" or padded "%NNd" in the path
            if re.findall(r"%(\d{1,2}d|d)", exported_path):
                # Check that all frames exist and
                # TODO: use a 3rd party library here (not clique as it is not maintained)
                check_image_sequence(exported_path)
            else:
                if not os.path.exists(exported_path):
                    raise PluginValidationError(
                        message=f"The file {exported_path} doesn't exists"
                    )
                self.logger.debug(f"Exported path {exported_path} exists.")
