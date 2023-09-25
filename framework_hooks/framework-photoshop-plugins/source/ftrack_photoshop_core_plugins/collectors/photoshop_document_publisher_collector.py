# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import tempfile

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants

from ftrack_framework_photoshop.app.base import BasePhotoshopApplication
from ftrack_framework_photoshop import constants as photoshop_constants


class PhotoshopDocumentPublisherCollectorPlugin(BasePlugin):
    '''Collects the current document data from Photoshop'''

    name = 'photoshop_document_publisher_collector'
    host_type = 'photoshop'
    plugin_type = constants.plugin.PLUGIN_COLLECTOR_TYPE

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=dict,
            required_output_value=None,
        )

    def run(self, context_data=None, data=None, options=None):
        export_option = options.get("export")
        if export_option and isinstance(export_option, list):
            export_option = export_option[0]
        export_object = []
        if export_option == 'document':
            # Fetch document name from Photoshop
            document_data = (
                BasePhotoshopApplication.instance().send_event_with_reply(
                    photoshop_constants.TOPIC_DOCUMENT_GET, {}
                )['result']
            )

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
                save_result = (
                    BasePhotoshopApplication.instance()
                    .instance()
                    .send_event_with_reply(
                        photoshop_constants.TOPIC_DOCUMENT_SAVE,
                        {'path': temp_path},
                    )['result']
                )
                if save_result == 'true':
                    document_data = (
                        BasePhotoshopApplication.instance()
                        .instance()
                        .send_event_with_reply(
                            photoshop_constants.TOPIC_DOCUMENT_GET, {}
                        )['result']
                    )
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
        return export_object
