import os
import tempfile

import nuke

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

from ftrack_framework_nuke.utils import save_temp


class ScriptCollectorPlugin(BasePlugin):
    '''Collect the current work script data from Nuke'''

    name = 'script_collector'

    def run(self, store):
        '''
        Saves Nuke script to temp if unsaved, and stores script path in the :obj:`store`
        '''

        script_path = nuke.root().name()
        if script_path == 'Root':
            # script is not saved, save it first.
            self.logger.warning('Nuke not saved, saving locally..')
            try:
                script_path = save_temp()
            except Exception as e:
                self.logger.exception(e)
                raise PluginExecutionError(
                    f'Could not save script locally: {e}'
                )

        component_name = self.options.get('component', 'main')
        store['components'][component_name]['collected_script'] = script_path
