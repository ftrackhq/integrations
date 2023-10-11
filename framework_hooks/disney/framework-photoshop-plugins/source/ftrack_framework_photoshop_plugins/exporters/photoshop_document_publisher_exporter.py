# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import tempfile
import shutil

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants


class PhotoshopDocumentPublisherExporterPlugin(BasePlugin):
    '''Save Photoshop document to temp location for publish'''

    name = 'photoshop_document_publisher_exporter'
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

        new_file_path = tempfile.NamedTemporaryFile(
            delete=False, suffix='.psd'
        ).name

        collected_objects = []
        for collector_result in list(
            data[self.plugin_step_name]['collector'].values()
        ):
            collected_objects.extend(collector_result)

        # Copy entire document
        document_data = collected_objects[0]
        document_path = document_data.get('full_path')

        self.logger.debug(
            "Copying Photoshop document from {} to {}".format(
                document_path, new_file_path
            )
        )
        shutil.copy(document_path, new_file_path)
        return [new_file_path]
