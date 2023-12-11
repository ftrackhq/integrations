# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import tempfile


from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants

from ftrack_framework_photoshop.rpc_cep import PhotoshopRPCCEP


class ImageExporterPlugin(BasePlugin):
    '''Save Photoshop document to temp location as an image for publish'''

    name = 'image_exporter'

    def run(self, store):
        '''
        Expects extension(format) from the :obj:`self.options`, stores the
        exported image path in the :obj:`store` under the component name.
        '''

        extension = self.options.get('extension') or '.jpg'

        component_name = self.options.get('component')

        new_file_path = tempfile.NamedTemporaryFile(
            delete=False, suffix=extension
        ).name

        try:
            # Get exiting RPC connection instance
            photoshop_connection = PhotoshopRPCCEP.instance()

            self.logger.debug(
                "Exporting Photoshop image to {}".format(new_file_path)
            )

            export_result = photoshop_connection.rpc(
                'exportDocument',
                [new_file_path, extension.replace('.', '')],
            )
        except Exception as e:
            self.logger.exception(e)
            self.message = 'Error exporting the image: {}'.format(e)
            self.status = constants.status.ERROR_STATUS
            return

        if isinstance(export_result, str):
            self.message = 'Error exporting the image: {}'.format(
                export_result
            )
            self.status = constants.status.ERROR_STATUS
            return
        store['components'][component_name]['exported_path'] = new_file_path
