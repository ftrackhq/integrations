# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_connect_pipeline_unreal import plugin
import os

import ftrack_api


class UnrealImageSequencePublisherValidatorPlugin(plugin.UnrealPublisherValidatorPlugin):
    '''Maya name publisher validator plugin'''

    plugin_name = 'unreal_image_sequence_publisher_validator'

    def run(self, context_data=None, data=None, options=None):
        '''Return True if all collected objects supplied in *data* has a
        supported file format'''

        collected_objects = []
        for collector in data:
            collected_objects.extend(collector['result'])

        supported_file_formats = options.get('supported_file_formats')

        for obj in collected_objects:
            # Get file extension
            file_extension = os.path.splitext(obj)[1].replace('.', '')
            # Make sure clean clique stuff
            if "[" in file_extension:
                file_extension = file_extension.split("[")[0].strip()
            if file_extension not in supported_file_formats:
                return False
        return True


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UnrealImageSequencePublisherValidatorPlugin(api_object)
    plugin.register()
