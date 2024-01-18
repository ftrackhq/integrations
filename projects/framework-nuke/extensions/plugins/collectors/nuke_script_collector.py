import os
import tempfile

import nuke

from ftrack_framework_core.plugin import BasePlugin


class NukeScriptCollectorPlugin(BasePlugin):
    '''Collect the current work script data from Nuke'''

    name = 'nuke_script_collector'

    def run(self, store):
        '''
        Queries and stores the current Nuke script path in the :obj:`store`
        '''

        component_name = self.options.get('component', 'main')
        script_name = nuke.root().name()
        self.logger.debug(f"Current script path: {script_name}.")
        store['components'][component_name]['script_name'] = script_name

        script_saved = nuke.root().modified()
        store['components'][component_name]['script_saved'] = not script_saved
        self.logger.debug(f"Script saved: {script_saved}.")
