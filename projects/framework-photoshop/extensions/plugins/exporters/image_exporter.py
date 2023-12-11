# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import tempfile


from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants

from ftrack_framework_photoshop.rpc_cep import PhotoshopRPCCEP


class ImageExporterPlugin(BasePlugin):
    '''Save Photoshop document to temp location as an image for publish'''

    name = 'image_exporter'

    def export(self, extension, destination_file):
        '''
        Copy the given *origin_file to *destination_file*
        '''

        # Get exiting RPC connection instance
        photoshop_connection = PhotoshopRPCCEP.instance()

        self.logger.debug(
            "Exporting Photoshop image to {}".format(destination_file)
        )

        return photoshop_connection.rpc(
            'exportDocument',
            [destination_file, extension.replace('.', '')],
        )

    def run(self, store):
        '''
        Expects collected_file in the <component_name> key of the given *store*
        and an export_destination from the :obj:`self.options`.
        '''

        extension = self.options.get('extension', '.jpg')

        component_name = self.options.get('component')

        new_file_path = tempfile.NamedTemporaryFile(
            delete=False, suffix=extension
        ).name

        export_result = self.export(extension, new_file_path)

        if not export_result or isinstance(export_result, str):
            self.message = 'Error exporting the reviewable: {}'.format(
                export_result
            )
            self.status = constants.status.ERROR_STATUS
            return
        store['components'][component_name]['exported_path'] = new_file_path
