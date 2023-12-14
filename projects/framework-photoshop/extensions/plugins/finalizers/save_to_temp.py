# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import tempfile

from ftrack_constants import status as status_constants
from ftrack_framework_plugin import BasePlugin

from ftrack_framework_photoshop.rpc_cep import PhotoshopRPCCEP


class SaveToTemp(BasePlugin):
    name = 'save_to_temp'

    def run(self, store):
        '''
        This method tells Photoshop to save the current document in a temp location.
        '''

        temp_path = tempfile.NamedTemporaryFile(
            delete=False, suffix='.psd'
        ).name

        try:
            # Get existing RPC connection instance
            photoshop_connection = PhotoshopRPCCEP.instance()

            self.logger.debug(
                'Telling Photoshop to save document to temp path: {}'.format(
                    temp_path
                )
            )

            save_result = photoshop_connection.rpc(
                'saveDocument',
                [temp_path],
            )
        except Exception as e:
            self.logger.exception(e)
            self.message = 'Exception saving document to temp: {}'.format(e)
            self.status = status_constants.EXCEPTION_STATUS
            return

        if isinstance(save_result, str):
            self.message = (
                'Error temp saving document in Photoshop: {}'.format(
                    save_result
                )
            )
            self.status = status_constants.ERROR_STATUS
            return
