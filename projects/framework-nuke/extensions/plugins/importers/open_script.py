# :coding: utf-8
# :copyright: Copyright (c) 2014-2024 ftrack

import nuke

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class OpenScriptPlugin(BasePlugin):
    '''Open the collected script in Nuke'''

    name = 'open_script'

    def run(self, store):
        '''
        Expects collected_path in the <component_name> key of the given *store*,
        opens it in Photoshop.
        '''
        component_name = self.options.get('component')

        script_path = store['components'][component_name].get('collected_path')

        try:
            open_result = nuke.scriptOpen(script_path)
        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(
                f'Exception opening script {script_path} in Nuke: {e}'
            )

        store['components'][component_name]['open_result'] = open_result
