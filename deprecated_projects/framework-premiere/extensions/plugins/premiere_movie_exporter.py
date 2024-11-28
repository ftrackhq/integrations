# :coding: utf-8
# :copyright: Copyright (c) 2014-2024 ftrack
import os

from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

from ftrack_utils.rpc import JavascriptRPC
import ftrack_framework_premiere


class PremiereMovieExporterPlugin(BasePlugin):
    name = 'premiere_movie_exporter'

    def run(self, store):
        '''
        Export the current active sequence to a movie file, save the exported
        path to the store under the component name.
        '''
        component_name = self.options.get('component')

        extension = 'mp4'

        preset_path = os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(ftrack_framework_premiere.__file__)
                )
            ),
            'resource',
            'presets',
            'reviewable.epr',
        )

        new_file_path = get_temp_path(filename_extension=extension)

        try:
            # Get existing RPC connection instance
            premiere_connection = JavascriptRPC.instance()

            self.logger.debug(
                f'Exporting Premiere movie to {new_file_path}, using preset: {preset_path}'
            )

            export_result = premiere_connection.rpc(
                'render',
                [
                    new_file_path.replace('\\', '/'),
                    preset_path.replace('\\', '/'),
                ],
            )
        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(f'Exception exporting the movie: {e}')

        if not export_result or isinstance(export_result, str):
            raise PluginExecutionError(
                f'Error exporting the movie: {export_result}'
            )

        store['components'][component_name]['exported_path'] = new_file_path
