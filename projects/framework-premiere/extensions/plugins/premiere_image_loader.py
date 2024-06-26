# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

from ftrack_utils.paths import check_image_sequence
from ftrack_utils.string import str_context
from ftrack_utils.rpc import JavascriptRPC


class PremiereImageLoaderPlugin(BasePlugin):
    name = 'premiere_image_loader'

    def run(self, store):
        '''
        Expects the path to image to load in *store*, loads the image in Premiere
        through RCP call.
        '''

        image_path = store.get('component_path')
        if not image_path:
            raise PluginExecutionError(f'No image path provided in store!')

        try:
            # Get existing RPC connection instance
            premiere_connection = JavascriptRPC.instance()

            component = self.session.query(
                f"Component where id={store['entity_id']}"
            ).first()
            context_path = (
                f"ftrack/{str_context(component['version']['asset'])}/"
                f"v{component['version']['version']:03}"
            )
            if store.get('is_sequence'):
                # Compile members
                sequence_metadata = check_image_sequence(
                    image_path, with_members=True
                )
                sequence_folder = os.path.dirname(image_path)
                load_result = premiere_connection.rpc(
                    'loadAsset',
                    [
                        sequence_folder.replace('\\', '/'),
                        context_path,
                        ','.join(sequence_metadata['members']),
                    ],
                )
            else:
                load_result = premiere_connection.rpc(
                    'loadAsset',
                    [image_path.replace('\\', '/'), context_path, ''],
                )

            if not load_result:
                raise PluginExecutionError(
                    f'Failed to load image in Premiere!'
                )

        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(f'Exception loading the image: {e}')

        store['load_result'] = load_result
