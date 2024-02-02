# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import nuke

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class NukeScriptOpenerPlugin(BasePlugin):
    '''Open the collected script in Nuke'''

    name = 'nuke_script_opener'

    def run(self, store):
        '''
        Expects collected_path in the <component> key of the given *store*,
        opens it in Nuke.
        '''
        component_name = self.options.get('component')

        script_path = store['components'][component_name].get('collected_path')

        self.logger.debug(f'Opening Nuke script: {script_path}')

        try:
            open_result = nuke.scriptOpen(script_path)
        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(
                f'Exception opening script {script_path} in Nuke: {e}'
            )

        store['components'][component_name]['open_result'] = open_result
