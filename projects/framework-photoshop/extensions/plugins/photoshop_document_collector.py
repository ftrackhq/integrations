# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

from ftrack_utils.rpc import JavascriptRPC


class PhotoshopDocumentCollectorPlugin(BasePlugin):
    name = 'photoshop_document_collector'

    def run(self, store):
        '''
        Collect the current document data from Photoshop
        and store in the given *store* on "document_name" and "document_saved"
        '''
        # Get existing RPC connection instance
        photoshop_connection = JavascriptRPC.instance()

        # Get document data containing the path
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

        # Check if document is saved
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

        document_name = (
            document_data.get('full_path') if document_data else None
        )

        if document_name:
            # Convert forward slashes to backslashes on Windows
            document_name = os.path.normpath(document_name)

        try:
            extension_format = self.options['extension_format']
        except Exception as error:
            raise PluginExecutionError(
                f"Could not provide extension_format: {error}"
            )

        self.logger.debug(f"Current document name is: {document_name}.")
        self.logger.debug(f"Extension format set to {extension_format}.")

        component_name = self.options.get('component', 'main')
        store['components'][component_name]['document_name'] = document_name
        store['components'][component_name][
            'extension_format'
        ] = extension_format
        store['components'][component_name][
            'document_saved'
        ] = document_saved_result

        # Hint: store the document data in the store if further validation on PSD is needed
        # store['components'][component_name]['collected_data'] = document_data
