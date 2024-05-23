# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os

from ftrack_utils.paths import get_temp_path, find_image_sequence

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

from ftrack_framework_harmony.utils.tcp_rpc import TCPRPCClient


class HarmonySequenceExporterPlugin(BasePlugin):
    name = 'harmony_sequence_exporter'

    def run(self, store):
        '''
        Tell Harmony to render the current scene to a temp directory, store the path
        in *store* under the component name.
        '''
        component_name = self.options.get('component')
        extension = self.options.get('export_type') or 'png'
        export_format = self.options.get('export_format') or ''

        temp_folder = get_temp_path()
        os.makedirs(temp_folder)

        prefix = "image"

        try:
            # Get existing RPC connection instance
            harmony_connection = TCPRPCClient.instance()

            self.logger.debug(
                f'Exporting Harmony image sequence to {temp_folder}'
            )

            render_response = harmony_connection.rpc(
                'renderSequence',
                [
                    '{}{}'.format(temp_folder.replace('\\', '/'), os.sep),
                    prefix,
                    extension.replace('.', ''),
                    export_format,
                ],
                timeout=-1,  # Wait indefinitely, we don't know how long the render will take
            )
        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(
                f'Exception exporting the image sequence: {e}'
            )

        if 'result' not in render_response:
            raise PluginExecutionError(
                f'Error exporting the image sequence: {render_response["error_message"]}'
            )

        # Collect the result
        sequence_path = find_image_sequence(temp_folder)

        if not sequence_path:
            raise PluginExecutionError(
                f'Could not locate rendered image sequence: {temp_folder}'
            )

        store['components'][component_name]['exported_path'] = sequence_path
