# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import tempfile
import os

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants
from ftrack_utils.framework.remote import get_integration_session_id


class PhotoshopDocumentPublisherCollectorPlugin(BasePlugin):
    '''Collects the current document data from Photoshop'''

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
        # Fetch document name from Photoshop
        document_data = self.event_manager.publish.remote_integration_rpc(
            get_integration_session_id(), "getDocumentData", fetch_reply=True
        )['result']

        self.logger.debug("Got PS document data: {}".format(document_data))

        if len(document_data or {}) == 0:
            self.message = (
                "Error exporting the scene: Please have an "
                "active work document before you can publish"
            )
            self.status = constants.status.ERROR_STATUS
            return []
        document_path = (
            document_data.get('full_path') if document_data else None
        )

        if (
            not document_path
            or document_data['saved'] is False
        ):
            # Document is not saved, save it first.
            self.logger.warning(
                'Photoshop document not saved, asking to save'
            )
            temp_path = tempfile.NamedTemporaryFile(
                delete=False, suffix='.psd'
            ).name
            save_result = (
                self.event_manager.publish.remote_integration_rpc(
                    get_integration_session_id(),
                    "saveDocument", [temp_path],
                    fetch_reply=True,
                )['result']
            )
            if save_result:
                # Now re-fetch document data
                document_data = (
                    self.event_manager.publish.remote_integration_rpc(
                        get_integration_session_id(),
                        "getDocumentData",
                        fetch_reply=True,
                    )['result']
                )
                document_path = (
                    document_data.get('full_path')
                    if document_data
                    else None
                )
        if len(document_path or '') == 0:
            self.message = (
                "Error exporting the scene: Please save the "
                "document with a name before publish"
            )

            self.status = constants.status.ERROR_STATUS
            return []
        export_object = [document_data]
        return export_object
