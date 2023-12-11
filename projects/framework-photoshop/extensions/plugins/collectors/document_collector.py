import os
import tempfile

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants
from ftrack_framework_photoshop.rpc_cep import PhotoshopRPCCEP


class DocumentCollectorPlugin(BasePlugin):
    name = 'document_collector'

    def run(self, store):
        '''
        Collect the current document data from Photoshop
        and store the collected_data in the given *store*.
        '''
        # Get exiting RPC connection instance
        photoshop_connection = PhotoshopRPCCEP.instance()

        try:
            document_saved_result = photoshop_connection.rpc('documentSaved')
        except Exception as e:
            self.logger.exception(e)
            self.message = (
                'Error querying if the document is saved: {}'.format(e)
            )
            self.status = constants.status.ERROR_STATUS
            return

        self.logger.debug(
            'Got Photoshop saved query result: {}'.format(
                document_saved_result
            )
        )

        if isinstance(document_saved_result, str):
            self.message = 'Photoshop document query failed: {}'.format(
                document_saved_result
            )
            self.status = constants.status.ERROR_STATUS
            return

        if not document_saved_result:
            # Document is not saved, save it first.
            self.logger.warning('Photoshop document not saved, asking to save')
            temp_path = tempfile.NamedTemporaryFile(
                delete=False, suffix='.psd'
            ).name
            save_result = photoshop_connection.rpc('saveDocument', [temp_path])
            # Will return a boolean containing the result.
            if isinstance(save_result, str):
                self.message = 'Error saving the document: {}'.format(
                    save_result
                )
                self.status = constants.status.ERROR_STATUS
                return
            elif save_result:
                self.logger.info('Document saved successfully')

        # Get document data
        try:
            document_data = photoshop_connection.rpc('getDocumentData')
        except Exception as e:
            self.logger.exception(e)
            self.message = 'Error querying the document data: {}'.format(e)
            self.status = constants.status.ERROR_STATUS
            return
        # Will return a dictionary with information about the document,
        # an empty dict is returned if no document is open.

        self.logger.debug(
            'Got Photoshop document data: {}'.format(document_data)
        )

        if len(document_data or {}) == 0:
            self.message = (
                'No document data available. Please have an '
                'active work document before you can publish'
            )
            self.status = constants.status.ERROR_STATUS
            return

        document_path = (
            document_data.get('full_path') if document_data else None
        )

        if len(document_path or '') == 0:
            self.message = (
                'Error exporting the document: Please save the '
                'document with a name before publish'
            )

            self.status = constants.status.ERROR_STATUS
            return
        elif not os.path.exists(document_path):
            self.message = (
                'Error exporting the document: Document does not exist: '
                '{}'.format(document_path)
            )

            self.status = constants.status.ERROR_STATUS
            return

        component_name = self.options.get('component', 'main')
        store['components'][component_name]['collected_data'] = document_data
