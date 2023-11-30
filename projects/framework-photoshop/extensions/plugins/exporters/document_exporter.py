# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import tempfile
import shutil

from ftrack_framework_plugin import BasePlugin


class DocumentExporterPlugin(BasePlugin):
    '''Save Photoshop document to temp location for publish'''

    name = 'document_exporter'

    def copy(self, origin_file, destination_file):
        '''
        Copy the given *origin_file to *destination_file*
        '''

        self.logger.debug(
            "Copying Photoshop document from {} to {}".format(
                origin_file, destination_file
            )
        )

        return shutil.copy(origin_file, destination_file)

    def run(self, store):
        '''
        Expects collected_file in the <component_name> key of the given *store*
        and an export_destination from the :obj:`self.options`.
        '''
        component_name = self.options.get('component')

        collected_data = store['components'][component_name]['collected_data']

        new_file_path = tempfile.NamedTemporaryFile(
            delete=False, suffix='.psd'
        ).name

        document_path = collected_data.get('full_path')

        store['components'][component_name]['exported_path'] = self.copy(
            document_path, new_file_path
        )
