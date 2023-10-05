# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import tempfile
import os

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants


class PhotoshopNativePublisherExporterPlugin(BasePlugin):
    '''Export image from Photoshop document to temp location for publish'''

    name = 'photoshop_image_publisher_exporter'
    host_type = 'photoshop'
    plugin_type = constants.plugin.PLUGIN_EXPORTER_TYPE
    extension = '.jpg'

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=list,
            required_output_value=None,
        )
        self.register_method(
            method_name='rename',
            required_output_type=None,
            required_output_value=None,
        )

    def run(self, context_data=None, data=None, options=None):
        '''
        Expects a dictionary with the previous collected data from the
        collector plugin in the given *data*. Also expects to have
        'export' type defined in the given *options*
        This method will return a list containing the new file path.
        '''

        new_file_path = tempfile.NamedTemporaryFile(
            delete=False, suffix=self.extension
        ).name

        is_document_publish = True
        collected_objects = []
        for value in list(data.values()):
            for collector_result in list(value['collector'].values()):
                collected_objects.extend(collector_result)

        if is_document_publish:
            # Export entire document
            document_path = collected_objects[0]

            self.logger.debug(
                "Exporting Photoshop document from {} to {}".format(
                    document_path, new_file_path
                )
            )

            result = self.event_manager.remote_integration_rpc(
                os.environ.get(
                    'FTRACK_INTEGRATION_SESSION_ID'
                ),
                "exportDocument", new_file_path, self.extension.replace('.', '')
            )['result']

            if result != 'true':
                return False, {"message": "Document JPG export failed!"}

        else:
            raise Exception(
                'Subset (layer) image export of document not supported'
            )

        return [new_file_path]
