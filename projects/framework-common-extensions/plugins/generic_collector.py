# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class GenericCollectorPlugin(BasePlugin):
    name = 'generic_collector'

    def run(self, store):
        '''
        Get folder_path and file_name from the :obj:`self.options`
        and store the collected_file in the given *store*.
        '''
        print(f"the options are:{self.options}")
