# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_utils.paths import get_temp_path
from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

from ftrack_utils.rpc import JavascriptRPC


class PremiereSaveToTempFinalizerPlugin(BasePlugin):
    name = 'premiere_save_to_temp_finalizer'

    def run(self, store):
        '''
        Tell Premiere to save the current project in a temp location.
        '''

        temp_path = get_temp_path(filename_extension='prproj')

        try:
            # Get existing RPC connection instance
            premiere_connection = JavascriptRPC.instance()

            self.logger.debug(
                f'Telling Premiere to save project to temp path: {temp_path}'
            )

            save_result = premiere_connection.rpc(
                'saveProjectAs',
                [temp_path.replace('\\', '/')],
            )
        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(
                f'Exception saving project to temp: {e}'
            )

        self.logger.debug(f"Premiere save result: {save_result}")

        if isinstance(save_result, str):
            raise PluginExecutionError(
                f'Error temp saving document in Premiere: {save_result}'
            )
