# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os

import ftrack_constants as constants
from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_photoshop.rpc_cep import PhotoshopRPCCEP


class OpenDocumentPlugin(BasePlugin):
    name = 'open_document'

    def run(self, store):
        '''
        Expects collected_path in the <component_name> key of the given *store*,
        opens it in Photoshop.
        '''
        component_name = self.options.get('component')

        collected_path = store['components'][component_name].get(
            'collected_path'
        )

        if not collected_path:
            message = "No path provided to open!"
            status = constants.status.ERROR_STATUS
            return status, message

        document_path = collected_path

        if not os.path.exists(document_path):
            message = "Document '{}' does not exist!".format(document_path)
            status = constants.status.ERROR_STATUS
            return status, message

        try:
            # Get existing RPC connection instance
            photoshop_connection = PhotoshopRPCCEP.instance()

            self.logger.debug(
                'Telling Photoshop to save document to: {}'.format(
                    document_path
                )
            )

            open_result = photoshop_connection.rpc(
                'openDocument',
                [document_path],
            )

        except Exception as e:
            self.logger.exception(e)
            message = (
                'Exception telling Photoshop to open document: {}'.format(e)
            )
            status = constants.status.EXCEPTION_STATUS
            return status, message

        if not open_result or isinstance(open_result, str):
            message = 'Error opening the document in Photoshop: {}'.format(
                open_result
            )
            status = constants.status.ERROR_STATUS
            return status, message

        store['components'][component_name]['open_result'] = open_result
