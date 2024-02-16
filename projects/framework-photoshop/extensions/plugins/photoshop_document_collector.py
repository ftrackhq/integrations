# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os

from ftrack_utils.paths import get_temp_path
from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

from ftrack_framework_photoshop.rpc_cep import PhotoshopRPCCEP


class PhotoshopDocumentCollectorPlugin(BasePlugin):
    name = 'document_collector'

    def run(self, store):
        '''
        Collect the current document data from Photoshop
        and store in the given *store* on "collected_data"
        '''
        # Get existing RPC connection instance
        photoshop_connection = PhotoshopRPCCEP.instance()

        try:
            document_saved_result = photoshop_connection.rpc('documentSaved')
        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(
                f'Exception querying if the document is saved: {e}'
            )

        self.logger.debug(
            f'Got Photoshop saved query result: {document_saved_result}'
        )

        if isinstance(document_saved_result, str):
            raise PluginExecutionError(
                f'Photoshop document query failed: {document_saved_result}'
            )

        if not document_saved_result:
            # Document is not saved, save it first.
            self.logger.warning('Photoshop document not saved, asking to save')
            temp_path = get_temp_path(filename_extension='.psd')
            save_result = photoshop_connection.rpc('saveDocument', [temp_path])
            # Will return a boolean containing the result.
            if not save_result or isinstance(save_result, str):
                raise PluginExecutionError(
                    f'An error occurred while saving the'
                    f' document: {save_result}'
                )
            elif save_result:
                self.logger.info('Document saved successfully')

        # Get document data
        try:
            document_data = photoshop_connection.rpc('getDocumentData')
        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(
                f'Exception querying the document data: {e}'
            )
        # Will return a dictionary with information about the document,
        # an empty dict is returned if no document is open.

        self.logger.debug(f'Got Photoshop document data: {document_data}')

        if not document_data:
            raise PluginExecutionError(
                'No document data available. Please have'
                ' an active work document before you can '
                'publish'
            )

        document_path = (
            document_data.get('full_path') if document_data else None
        )

        if not document_path:
            raise PluginExecutionError(
                'Error exporting the document: Please save the '
                'document with a name before publish'
            )

        # Convert forward slashes to backslashes on Windows
        document_path = os.path.normpath(document_path)

        if not os.path.exists(document_path):
            raise PluginExecutionError(
                'Error exporting the document: Document does not exist: '
                f'{document_path}'
            )

        component_name = self.options.get('component', 'main')
        store['components'][component_name]['collected_data'] = document_data
