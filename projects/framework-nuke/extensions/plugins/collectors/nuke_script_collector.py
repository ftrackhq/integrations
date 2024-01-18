# :coding: utf-8
# :copyright: Copyright (c) 2014-2024 ftrack

import nuke

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class NukeScriptCollectorPlugin(BasePlugin):
    '''Collect the current work script data from Nuke'''

    name = 'nuke_script_collector'

    def run(self, store):
        '''
        Queries and stores the current Nuke script path in the :obj:`store`
        '''

        try:
            export_type = self.options['export_type']
        except Exception as error:
            raise PluginExecutionError(
                f"Failed to provide export_type: {error}"
            )

        component_name = self.options.get('component', 'main')

        store['components'][component_name]['export_type'] = export_type
        self.logger.debug(f"Export type: {export_type}.")

        script_name = nuke.root().name()
        self.logger.debug(f"Current script path: {script_name}.")
        store['components'][component_name]['script_name'] = script_name

        script_saved = not nuke.root().modified()
        store['components'][component_name]['script_saved'] = not script_saved
        self.logger.debug(f"Script saved: {script_saved}.")
