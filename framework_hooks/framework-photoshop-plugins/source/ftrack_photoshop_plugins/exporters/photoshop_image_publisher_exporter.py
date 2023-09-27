# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import tempfile
import shutil

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants

from ftrack_framework_photoshop.app.base import BasePhotoshopApplication
from ftrack_framework_photoshop import constants as photoshop_constants


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

        collected_objects = []
        is_document_publish = False
        for collector in data:
            collected_objects.extend(collector['result'])
            if collector.get('options', {}).get('export') == 'document':
                is_document_publish = True

        if is_document_publish:
            # Export entire document
            document_path = collected_objects[0]

            self.logger.debug(
                "Exporting Photoshop document from {} to {}".format(
                    document_path, new_file_path
                )
            )

            result = BasePhotoshopApplication.instance().send_event_with_reply(
                photoshop_constants.TOPIC_DOCUMENT_EXPORT,
                {
                    'path': new_file_path,
                    'format': self.extension.replace('.', ''),
                },
            )['result']

            if result != 'true':
                return False, {"message": "Document JPG export failed!"}

        else:
            raise Exception(
                'Subset (layer) image export of document not supported'
            )

        return [new_file_path]
