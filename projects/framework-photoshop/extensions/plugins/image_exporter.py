# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import tempfile

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

from ftrack_framework_photoshop.rpc_cep import PhotoshopRPCCEP


class ImageExporterPlugin(BasePlugin):
    '''Save Photoshop document to temp location as an image for publish'''

    name = 'image_exporter'

    def run(self, store):
        '''
        Expects extension(format) from the :obj:`self.options`, stores the
        exported image path in the :obj:`store` under the component name.
        '''

        extension = self.options.get('extension', '.jpg')

        component_name = self.options.get('component')

        new_file_path = tempfile.NamedTemporaryFile(
            delete=False, suffix=extension
        ).name

        try:
            # Get existing RPC connection instance
            photoshop_connection = PhotoshopRPCCEP.instance()

            self.logger.debug(f'Exporting Photoshop image to {new_file_path}')

            export_result = photoshop_connection.rpc(
                'exportDocument',
                [new_file_path.replace('\\', '/'), extension.replace('.', '')],
            )
        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(f'Exception exporting the image: {e}')

        if not export_result or isinstance(export_result, str):
            raise PluginExecutionError(
                f'Error exporting the image: {export_result}'
            )

        store['components'][component_name]['exported_path'] = new_file_path
