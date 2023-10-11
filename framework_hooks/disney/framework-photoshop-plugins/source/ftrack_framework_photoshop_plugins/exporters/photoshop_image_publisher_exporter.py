# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import tempfile
import os

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants
from ftrack_utils.framework.remote import get_integration_session_id


class PhotoshopImagePublisherExporterPlugin(BasePlugin):
    '''Export image from Photoshop document to temp location for publish'''

    name = 'photoshop_image_publisher_exporter'
    host_type = constants.host.PYTHON_HOST_TYPE
    plugin_type = constants.plugin.PLUGIN_EXPORTER_TYPE

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=list,
            required_output_value=None,
        )

    def run(self, context_data=None, data=None, options=None):
        '''
        Expects a dictionary with the previous collected data from the
        collector plugin in the given *data*. Also expects to have
        'export' type defined in the given *options*
        This method will return a list containing the new file path.
        '''

        extension = options.get('extension') or '.jpg'

        new_file_path = tempfile.NamedTemporaryFile(
            delete=False, suffix=extension
        ).name

        collected_objects = []
        for collector_result in list(
            data[self.plugin_step_name]['collector'].values()
        ):
            collected_objects.extend(collector_result)

        # Export entire document
        document_path = collected_objects[0]

        self.logger.debug(
            "Exporting Photoshop document from {} to {}".format(
                document_path, new_file_path
            )
        )

        result = self.event_manager.publish.remote_integration_rpc(
            get_integration_session_id(),
            "exportDocument",
            [new_file_path, extension.replace('.', '')],
            fetch_reply=True,
        )['result']
        # Expect boolean result from Photoshop, or a string with error message
        # if an exception occurs during export.

        if not result:
            self.message = "Document JPG export failed!"
            self.status = constants.status.ERROR_STATUS
            return []
        elif isinstance(result, str):
            self.message = "Error exporting image: {}".format(result)
            self.status = constants.status.ERROR_STATUS
            return []

        return [new_file_path]
