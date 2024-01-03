# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import sys
import subprocess

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class OpenFilePlugin(BasePlugin):
    name = 'open_file'

    def open_file(self, source_file):
        '''
        Open *source_file* in the default application for the current platform.
        '''

        if not os.path.exists(source_file):
            raise PluginExecutionError("File does not exist!")

        if sys.platform == 'win32':
            return subprocess.Popen(['start', source_file]).wait() == 0
        elif sys.platform == 'darwin':
            return subprocess.Popen(['open', source_file]).wait() == 0
        else:
            raise PluginExecutionError('Unsupported platform')

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
            raise PluginExecutionError("No path provided to open!")

        store['components'][component_name]['open_result'] = self.open_file(
            collected_path
        )
