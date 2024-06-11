# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import nuke

from ftrack_utils.paths import get_temp_path
from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class NukeImageLoaderPlugin(BasePlugin):
    '''Load an image into Nuke'''

    name = 'nuke_image_loader'

    def run(self, store):
        '''
        Expects the image to load in the :obj:`self.options`, loads the image
        '''
        image_path = store.get('component_path')
        if not image_path:
            raise PluginExecutionError(f'No image path provided in store!')

        n = nuke.nodes.Read()
        n['file'].fromUserText(image_path)

        self.logger.debug(f'Created image read node: {n}')

        if not image_path:
            raise PluginExecutionError(message='No path provided to load!')
