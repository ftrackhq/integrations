# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import tempfile
import os

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants
from ftrack_utils.framework import get_integration_session_id

class PhotoshopDocumentPublisherCollectorPlugin(BasePlugin):
    '''Collects the current document data from Photoshop'''

    name = 'photoshop_document_publisher_collector'
    host_type = 'photoshop'
    plugin_type = constants.plugin.PLUGIN_COLLECTOR_TYPE

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=list,
            required_output_value=None,
        )

    def run(self, context_data=None, data=None, options=None):
        export_option = options.get("export")
        if export_option and not isinstance(export_option, str):
            export_option = export_option[0]
        export_object = []
        if export_option == 'document':
            # Fetch document name from Photoshop
            document_data = self.event_manager.publish.remote_integration_rpc(
                get_integration_session_id(),
                "getDocument"
            )['result']

            self.logger.debug("Got PS document data: {}".format(document_data))

            document_path = (
                document_data.get('full_path') if document_data else None
            )

            if (
                len(document_path or '') == 0
                or document_data['saved'] is False
            ):
                # Document is not saved, save it first.
                self.logger.warning(
                    'Photoshop document not saved, asking to save'
                )
                temp_path = tempfile.NamedTemporaryFile(
                    delete=False, suffix='.psd'
                ).name
                save_result = self.event_manager.publish.remote_integration_rpc(
                    get_integration_session_id(),
                    "saveDocument", temp_path
                )['result']
                if save_result:
                    # Now re-fetch document data
                    document_data = self.event_manager.publish.remote_integration_rpc(
                        get_integration_session_id(),
                        "getDocumentData"
                    )['result']
                    document_path = (
                        document_data.get('full_path')
                        if document_data
                        else None
                    )
            if len(document_path or '') == 0:
                return False, {
                    "message": "Error exporting the scene: Please save the "
                    "document with a name before publish"
                }
            export_object = [document_data]
        else:
            raise Exception('Only "document" export option is supported')
        return export_object
