# :coding: utf-8
# :copyright: Copyright (c) 2014-2024 ftrack
import os

from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

from ftrack_framework_premiere import rpc_cep
from ftrack_framework_premiere.rpc_cep import PremiereRPCCEP


class PremiereSceneExporterPlugin(BasePlugin):
    name = 'premiere_movie_exporter'

    def run(self, store):
        '''
        If export type is selection then export the selection objects in the
        scene with the options passed. Otherwise, set the current scene path to
        the store.
        '''
        component_name = self.options.get('component')

        extension = 'mp4'

        preset_path = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(rpc_cep.__file__))
            ),
            'resource',
            'presets',
            'reviewable.epr',
        )

        new_file_path = get_temp_path(filename_extension=extension)

        try:
            # Get existing RPC connection instance
            photoshop_connection = PremiereRPCCEP.instance()

            self.logger.debug(f'Exporting Photoshop image to {new_file_path}')

            export_result = photoshop_connection.rpc(
                'render',
                [
                    new_file_path.replace('\\', '/'),
                    preset_path.replace('\\', '/'),
                ],
            )
        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(f'Exception exporting the image: {e}')

        if not export_result or isinstance(export_result, str):
            raise PluginExecutionError(
                f'Error exporting the image: {export_result}'
            )

        store['components'][component_name]['exported_path'] = new_file_path
