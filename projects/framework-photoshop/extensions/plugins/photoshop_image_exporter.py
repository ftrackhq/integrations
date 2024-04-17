# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_utils.paths import get_temp_path
from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

from ftrack_framework_photoshop.rpc_cep import JavascriptRPC


class PhotoshopImageExporterPlugin(BasePlugin):
    name = 'photoshop_image_exporter'

    def run(self, store):
        '''
        Expects extension(format) from the :obj:`self.options`, exports and
        image to temp location and stores the path in the  :obj:`store` under
        the component name.
        '''

        component_name = self.options.get('component')

        extension = store['components'][component_name].get('export_type')
        if not extension:
            raise PluginExecutionError(f'No image extension provided!')

        new_file_path = get_temp_path(filename_extension=extension)

        try:
            # Get existing RPC connection instance
            photoshop_connection = JavascriptRPC.instance()

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
