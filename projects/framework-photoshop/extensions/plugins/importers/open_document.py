# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os

import ftrack_constants.framework as constants
from ftrack_framework_plugin import BasePlugin

from ftrack_framework_photoshop.rpc_cep import PhotoshopRPCCEP


class OpenDocumentPlugin(BasePlugin):
    name = 'open_document'

    def open_document(self, document_path):
        '''
        Open *source_file* in photoshop
        '''

        # Get exiting RPC connection instance
        photoshop_connection = PhotoshopRPCCEP.instance()

        self.logger.debug(
            'Telling Photoshop to save document to: {}'.format(document_path)
        )

        return photoshop_connection.rpc(
            'openDocument',
            [document_path],
        )

    def run(self, store):
        '''
        Expects collected_file in the <component_name> key of the given *store*
        and an export_destination from the :obj:`self.options`.
        '''
        component_name = self.options.get('component')

        collected_path = store['components'][component_name].get(
            'collected_path'
        )

        if not collected_path:
            self.message = "No path provided to open!"
            self.status = constants.status.ERROR_STATUS

        document_path = collected_path

        if not os.path.exists(document_path):
            self.message = "Document '{}' does not exist!".format(
                document_path
            )
            self.status = constants.status.ERROR_STATUS
            return

        open_result = self.open_document(document_path)

        if isinstance(open_result, str):
            self.message = (
                'Error opening the document in Photoshop: {}'.format(
                    open_result
                )
            )
            self.status = constants.status.ERROR_STATUS
            return

        store['components'][component_name]['open_result'] = open_result
