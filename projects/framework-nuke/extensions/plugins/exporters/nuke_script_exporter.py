# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import nuke

from ftrack_utils.paths import get_temp_path
from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class NukeScriptExporterPlugin(BasePlugin):
    '''Save Nuke script to temp location for publish'''

    name = 'nuke_script_exporter'

    def run(self, store):
        '''
        Expects collected_script in the <component_name> key of the
        given *store*, stores the exported script path in the :obj:`store`
        '''
        component_name = self.options.get('component')

        script_name = store['components'][component_name]['script_name']
        export_type = store['components'][component_name].get('export_type')

        if export_type == 'selection':
            # Check if any node is selected
            if not nuke.selectedNodes():
                raise PluginExecutionError(
                    message='No nodes selected for export'
                )

            self.logger.debug('Exporting selection to a temp file for publish')
            exported_path = get_temp_path(filename_extension='.nk')

            self.logger.debug(f'Exporting selected nodes to: {exported_path}')
            try:
                nuke.nodeCopy(exported_path)
            except Exception as e:
                raise PluginExecutionError(
                    message=f"Couldn't export selected nodes: {e}"
                )
        else:
            exported_path = script_name

        self.logger.debug(f'Nuke script to publish: {exported_path}')

        store['components'][component_name]['exported_path'] = exported_path
