# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os

import nuke

from ftrack_utils.paths import check_image_sequence
from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class NukeImageLoaderPlugin(BasePlugin):
    '''Load an image or sequence into Nuke'''

    name = 'nuke_image_loader'

    def run(self, store):
        '''
        Expects the image to load in the :obj:`self.options`, loads the image
        '''
        image_path = store.get('component_path')
        if not image_path:
            raise PluginExecutionError(f'No image path provided in store!')

        n = nuke.nodes.Read()

        sequence_metadata = None
        if store.get('is_sequence'):
            # Expect path to be on the form folder/plate.%d.exr [1-35], convert to Nuke loadable
            # format
            sequence_metadata = check_image_sequence(image_path)
            image_path = image_path[: image_path.rfind(' ')].replace(
                '%d', '%0{}d'.format(sequence_metadata['padding'])
            )
        else:
            # Check that file exists
            if not os.path.exists(image_path):
                raise PluginExecutionError(
                    f'Image file does not exist: {image_path}'
                )

        n['file'].fromUserText(image_path)

        self.logger.debug(f'Created image read node, reading: {image_path}')

        if store.get('is_sequence'):
            n['first'].setValue(sequence_metadata['start'])
            n['last'].setValue(sequence_metadata['end'])
            self.logger.debug(
                'Image sequence frame range set: '
                f'{sequence_metadata["start"]}-{sequence_metadata["end"]}'
            )
