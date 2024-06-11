# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os
import re

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginValidationError


class ExportedPathsValidatorPlugin(BasePlugin):
    '''
    Plugin to validate if exported_paths of all components in the store exists.

    Expected format: folder/image.%d.jpg [1-35]
    '''

    name = 'exported_paths_validator'

    def check_image_sequence(self, path):
        '''Check if the image sequence pointed out by *path* exists.'''
        directory, basename = os.path.split(path)

        p_pos = basename.find('%')
        d_pos = basename.find('d', p_pos)
        exp = basename[p_pos : d_pos + 1]

        pad = 0
        if d_pos > p_pos + 2:
            pad = int(basename[p_pos + 1 : d_pos])

        ws_pos = basename.rfind(' ')
        dash_pos = basename.find('-', ws_pos)

        prefix = basename[:p_pos]
        suffix = basename[d_pos + 1 : ws_pos]

        start = int(basename[ws_pos + 2 : dash_pos])
        end = int(basename[dash_pos + 1 : -1])

        self.logger.debug(
            f'Looking for frames {start}>{end} in directory {directory} starting '
            f'with {prefix}, ending with {suffix} (padding: {pad})'
        )

        for frame in range(start, end + 1):
            filename = f'{prefix}{exp % frame}{suffix}'
            test_path = os.path.join(directory, filename)
            if not os.path.exists(test_path):
                raise PluginValidationError(
                    f'Image sequence member {frame} not '
                    f'found @ "{test_path}"!'
                )
            self.logger.debug(f'Frame {frame} verified: {filename}')

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
                self.check_image_sequence(exported_path)
            else:
                if not os.path.exists(exported_path):
                    raise PluginValidationError(
                        message=f"The file {exported_path} doesn't exists"
                    )
                self.logger.debug(f"Exported path {exported_path} exists.")
