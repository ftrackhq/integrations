# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os

from ftrack_utils.paths import get_temp_path

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

        sequence_path = get_temp_path()
        os.makedirs(sequence_path)

        prefix = "image"
        extension = (
            store['components'][component_name].get('export_type') or "png"
        )

        try:
            # Get existing RPC connection instance
            harmony_connection = TCPRPCClient.instance()

            self.logger.debug(
                f'Exporting Harmony image sequence to {sequence_path}'
            )

            export_result = harmony_connection.rpc(
                'renderSequence',
                [
                    "{}{}".format(sequence_path, os.sep),
                    prefix,
                    extension.replace('.', ''),
                ],
            )
        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(
                f'Exception exporting the image sequence: {e}'
            )

        if not export_result or isinstance(export_result, str):
            raise PluginExecutionError(
                f'Error exporting the image sequence: {export_result}'
            )

        store['components'][component_name]['exported_path'] = sequence_path
