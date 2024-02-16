# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_utils.paths import get_temp_path
from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

from ftrack_framework_photoshop.rpc_cep import PhotoshopRPCCEP


class PhotoshopSaveToTemp(BasePlugin):
    name = 'save_to_temp'

    def run(self, store):
        '''
        Tell Photoshop to save the current document in a temp location.
        '''

        temp_path = get_temp_path(filename_extension='.psd')
        try:
            # Get existing RPC connection instance
            photoshop_connection = PhotoshopRPCCEP.instance()

            self.logger.debug(
                f'Telling Photoshop to save document to temp path: {temp_path}'
            )

            save_result = photoshop_connection.rpc(
                'saveDocument',
                [temp_path],
            )
        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(
                f'Exception saving document to temp: {e}'
            )

        self.logger.debug(f"Photoshop save result: {save_result}")

        if isinstance(save_result, str):
            raise PluginExecutionError(
                f'Error temp saving document in Photoshop: {save_result}'
            )
