# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import sys
import subprocess

import ftrack_constants as constants
from ftrack_framework_plugin import BasePlugin


class OpenFilePlugin(BasePlugin):
    name = 'open_file'

    def open_file(self, source_file):
        '''
        Open *source_file* in the default application for the current platform.
        '''

        if sys.platform == 'win32':
            return subprocess.Popen(['start', source_file]).wait() == 0
        elif sys.platform == 'darwin':
            return subprocess.Popen(['open', source_file]).wait() == 0
        else:
            raise Exception('Unsupported platform')

    def run(self, store):
        '''
        Expects collected_file in the <component_name> key of the given *store*
        and an export_destination from the :obj:`self.options`.
        '''
        component_name = self.options.get('component')

        collected_path = store['components'][component_name].get(
            'collected_path'
        )

        if not collected_path:
            self.message = "No path provided to open!"
            self.status = constants.status.ERROR_STATUS

        store['components'][component_name]['open_result'] = self.open_file(
            collected_path
        )
