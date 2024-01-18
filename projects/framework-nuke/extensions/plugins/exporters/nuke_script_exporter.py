# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import tempfile
import shutil

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

        self.logger.debug(f'Nuke script to publish: {script_name}')

        store['components'][component_name]['exported_path'] = script_name
