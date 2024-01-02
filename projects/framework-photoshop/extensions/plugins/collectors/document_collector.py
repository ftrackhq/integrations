import os
import tempfile

import ftrack_constants as constants
from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_photoshop.rpc_cep import PhotoshopRPCCEP


class DocumentCollectorPlugin(BasePlugin):
    name = 'document_collector'

    def run(self, store):
        '''
        Collect the current document data from Photoshop
        and store the collected_data in the given *store*.
        '''
        # Get existing RPC connection instance
        photoshop_connection = PhotoshopRPCCEP.instance()

        try:
            document_saved_result = photoshop_connection.rpc('documentSaved')
        except Exception as e:
            self.logger.exception(e)
            message = 'Exception querying if the document is saved: {}'.format(
                e
            )
            status = constants.status.EXCEPTION_STATUS
            return status, message

        self.logger.debug(
            'Got Photoshop saved query result: {}'.format(
                document_saved_result
            )
        )

        if isinstance(document_saved_result, str):
            message = 'Photoshop document query failed: {}'.format(
                document_saved_result
            )
            status = constants.status.ERROR_STATUS
            return status, message

        if not document_saved_result:
            # Document is not saved, save it first.
            self.logger.warning('Photoshop document not saved, asking to save')
            temp_path = tempfile.NamedTemporaryFile(
                delete=False, suffix='.psd'
            ).name
            save_result = photoshop_connection.rpc('saveDocument', [temp_path])
            # Will return a boolean containing the result.
            if not save_result or isinstance(save_result, str):
                message = (
                    'An error occured while saving the document: {}'.format(
                        save_result
                    )
                )
                status = constants.status.ERROR_STATUS
                return status, message
            elif save_result:
                self.logger.info('Document saved successfully')

        # Get document data
        try:
            document_data = photoshop_connection.rpc('getDocumentData')
        except Exception as e:
            self.logger.exception(e)
            message = 'Exception querying the document data: {}'.format(e)
            status = constants.status.EXCEPTION_STATUS
            return status, message
        # Will return a dictionary with information about the document,
        # an empty dict is returned if no document is open.

        self.logger.debug(
            'Got Photoshop document data: {}'.format(document_data)
        )

        if not document_data:
            message = (
                'No document data available. Please have an '
                'active work document before you can publish'
            )
            status = constants.status.ERROR_STATUS
            return status, message

        document_path = (
            document_data.get('full_path') if document_data else None
        )

        if not document_path:
            message = (
                'Error exporting the document: Please save the '
                'document with a name before publish'
            )

            status = constants.status.ERROR_STATUS
            return status, message

        # Convert forward slashes to backslashes on Windows
        document_path = os.path.normpath(document_path)

        if not os.path.exists(document_path):
            message = (
                'Error exporting the document: Document does not exist: '
                '{}'.format(document_path)
            )

            status = constants.status.ERROR_STATUS
            return status, message

        component_name = self.options.get('component', 'main')
        store['components'][component_name]['collected_data'] = document_data
