# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import tempfile
import os

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants
from ftrack_utils.framework.remote import get_integration_session_id


class PhotoshopDocumentPublisherCollectorPlugin(BasePlugin):
    name = 'photoshop_document_publisher_collector'
    host_type = constants.host.PYTHON_HOST_TYPE
    plugin_type = constants.plugin.PLUGIN_COLLECTOR_TYPE

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=list,
            required_output_value=None,
        )

    def run(self, context_data=None, data=None, options=None):
        '''Collect the current document data from Photoshop'''

        # Check if document is open and saved

        document_saved_result = (
            self.event_manager.publish.remote_integration_rpc(
                get_integration_session_id(), 'documentSaved', fetch_reply=True
            )['result']
        )

        if isinstance(document_saved_result, str):
            self.message = 'Error exporting the document: {}'.format(
                document_saved_result
            )
            self.status = constants.status.ERROR_STATUS
            return []

        if not document_saved_result:
            # Document is not saved, save it first.
            self.logger.warning('Photoshop document not saved, asking to save')
            temp_path = tempfile.NamedTemporaryFile(
                delete=False, suffix='.psd'
            ).name
            save_result = self.event_manager.publish.remote_integration_rpc(
                get_integration_session_id(),
                "saveDocument",
                [temp_path],
                fetch_reply=True,
            )['result']
            # Will return a boolean containing the result.
            if isinstance(save_result, str):
                self.message = 'Error saving the document: {}'.format(
                    save_result
                )
                self.status = constants.status.ERROR_STATUS
                return []
            elif save_result:
                self.logger.info('Document saved successfully')

        # Get document data
        document_data = self.event_manager.publish.remote_integration_rpc(
            get_integration_session_id(), 'getDocumentData', fetch_reply=True
        )['result']
        # Will return a dictionary with information about the document,
        # an empty dict is returned if no document is open.

        self.logger.debug('Got PS document data: {}'.format(document_data))

        if len(document_data or {}) == 0:
            self.message = (
                'Error exporting the document: Please have an '
                'active work document before you can publish'
            )
            self.status = constants.status.ERROR_STATUS
            return []

        document_path = (
            document_data.get('full_path') if document_data else None
        )

        if len(document_path or '') == 0:
            self.message = (
                'Error exporting the document: Please save the '
                'document with a name before publish'
            )

            self.status = constants.status.ERROR_STATUS
            return []
        elif not os.path.exists(document_path):
            self.message = (
                'Error exporting the document: Document does not exist: '
                '{}'.format(document_path)
            )

            self.status = constants.status.ERROR_STATUS
            return []

        export_object = [document_data]
        return export_object
