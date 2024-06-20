# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_utils.paths import get_temp_path
from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

from ftrack_utils.rpc import JavascriptRPC


class PhotoshopImageLoaderPlugin(BasePlugin):
    name = 'photoshop_image_loader'

    def run(self, store):
        '''
        Expects the path to image to load in *store*, loads the image in Photoshop
        through RCP call.
        '''

        image_path = store.get('component_path')
        if not image_path:
            raise PluginExecutionError(f'No image path provided in store!')

        try:
            # Get existing RPC connection instance
            photoshop_connection = JavascriptRPC.instance()

            load_result = photoshop_connection.rpc(
                'loadImage',
                [image_path.replace('\\', '/')],
            )
        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(f'Exception loading the image: {e}')

        store['load_result'] = load_result
