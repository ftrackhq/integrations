import os
import tempfile

import nuke

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

from ftrack_framework_nuke.utils import save_temp


class NukeScriptCollectorPlugin(BasePlugin):
    '''Collect the current work script data from Nuke'''

    name = 'script_collector'

    def run(self, store):
        '''
        Queries and stores the current Nuke script path in the :obj:`store`
        '''

        component_name = self.options.get('component', 'main')
        script_path = nuke.root().name()
        store['components'][component_name]['collected_script'] = script_path
