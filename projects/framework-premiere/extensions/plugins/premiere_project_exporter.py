# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import shutil

from ftrack_utils.paths import get_temp_path
from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class PremiereProjectExporterPlugin(BasePlugin):
    name = 'premiere_project_exporter'

    def run(self, store):
        '''
        Expects full_path in collected_data in the <component_name> key of the
        given *store*, copies it to temp location and stores the exported project
        path in the :obj:`store`
        '''
        component_name = self.options.get('component')
        project_path = store['components'][component_name]['project_name']

        new_file_path = get_temp_path(filename_extension='prproj')

        self.logger.debug(
            f'Copying Premiere project from {project_path} to {new_file_path}'
        )

        try:
            store['components'][component_name]['exported_path'] = shutil.copy(
                project_path, new_file_path
            )
        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(f'Exception copying the project: {e}')
