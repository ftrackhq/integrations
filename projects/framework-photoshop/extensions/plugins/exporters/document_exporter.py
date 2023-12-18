# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import tempfile
import shutil

import ftrack_constants as constants
from ftrack_framework_core.plugin import BasePlugin


class DocumentExporterPlugin(BasePlugin):
    '''Save Photoshop document to temp location for publish'''

    name = 'document_exporter'

    def run(self, store):
        '''
        Expects full_path in collected_data in the <component_name> key of the
        given *store*, stores the exported document path in the :obj:`store`
        '''
        component_name = self.options.get('component')

        collected_data = store['components'][component_name]['collected_data']

        new_file_path = tempfile.NamedTemporaryFile(
            delete=False, suffix='.psd'
        ).name

        document_path = collected_data.get('full_path')

        self.logger.debug(
            "Copying Photoshop document from {} to {}".format(
                document_path, new_file_path
            )
        )

        try:
            store['components'][component_name]['exported_path'] = shutil.copy(
                document_path, new_file_path
            )
        except Exception as e:
            self.logger.exception(e)
            self.message = 'Exception copying the document: {}'.format(e)
            self.status = constants.status.EXCEPTION_STATUS
            return
