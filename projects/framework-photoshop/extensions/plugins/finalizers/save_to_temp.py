# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import tempfile

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants

from ftrack_framework_photoshop.rpc_cep import PhotoshopRPCCEP


class SaveToTemp(BasePlugin):
    name = 'save_to_temp'

    def save_temp(self, temp_path):
        # Get exiting RPC connection instance
        photoshop_connection = PhotoshopRPCCEP.instance()

        self.logger.debug(
            'Telling Photoshop to save document to temp path: {}'.format(
                temp_path
            )
        )

        return photoshop_connection.rpc(
            'saveDocument',
            [temp_path],
        )

    def run(self, store):
        '''
        This method tells Photoshop to save the current document in a temp location.
        '''

        temp_path = tempfile.NamedTemporaryFile(
            delete=False, suffix='.psd'
        ).name

        save_result = self.save_temp(temp_path)

        if isinstance(save_result, str):
            self.message = (
                'Error temp saving document in Photoshop: {}'.format(
                    save_result
                )
            )
            self.status = constants.status.ERROR_STATUS
            return
