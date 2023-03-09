# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_connect_pipeline_unreal import plugin
import clique

import ftrack_api


class UnrealImageSequencePublisherValidatorPlugin(
    plugin.UnrealPublisherValidatorPlugin
):
    '''Maya name publisher validator plugin'''

    plugin_name = 'unreal_image_sequence_publisher_validator'

    def run(self, context_data=None, data=None, options=None):
        '''Return True if all collected objects supplied in *data* is an image
        sequence and has a supported file format'''

        supported_file_formats = ["exr", "jpg", "bmp", "png"]

        media_path = None
        for collector in data:
            for result in collector['result']:
                # We are only interested on the media_path
                media_path = result.get('media_path')

        if media_path:
            try:
                collection = clique.parse(media_path)
                if str(collection.tail).lower().split(".")[-1] in supported_file_formats:
                    return True
                return False
            except Exception as e:
                self.logger.error(
                    "Unsupported media path: {} \n "
                    "With error message: {}".format(media_path, e)
                )
                return False
        return True


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UnrealImageSequencePublisherValidatorPlugin(api_object)
    plugin.register()
