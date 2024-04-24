# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

from ftrack_utils.rpc import JavascriptRPC


class PremiereProjectCollectorPlugin(BasePlugin):
    name = 'premiere_project_collector'

    def run(self, store):
        '''
        Collect the current project path from Premiere
        and store in the given *store* on "project_name"
        '''
        # Get existing RPC connection instance
        premiere_connection = JavascriptRPC.instance()

        # Get project data containing the path
        try:
            project_path = premiere_connection.rpc('getProjectPath')
        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(
                f'Exception querying the project data: {e}'
            )

        # Will return a path to the .prproj file, or an error message if no
        # project is open.

        self.logger.debug(f'Got Premiere project path: {project_path}')

        if not project_path or project_path.startswith('Error:'):
            raise PluginExecutionError(
                'No project data available. Please have'
                ' an active work project before you can '
                'publish'
            )

        component_name = self.options.get('component', 'main')
        store['components'][component_name]['project_name'] = project_path
