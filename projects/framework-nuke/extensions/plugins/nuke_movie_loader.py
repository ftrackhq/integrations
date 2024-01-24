# :coding: utf-8
# :copyright: Copyright (c) 2014-2024 ftrack

import nuke

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class NukeMovieLoaderPlugin(BasePlugin):
    '''Open the collected script in Nuke'''

    name = 'nuke_movie_loader'

    def run(self, store):
        '''
        Expects collected_path in the <component> key of the given *store*,
        opens it in Nuke.
        '''

        asset_path = self.options['collected_path']

        self.logger.debug(f'Loading Nuke asset: {asset_path}')

        resulting_node = nuke.createNode('Read', inpanel=False)
        resulting_node['file'].fromUserText(asset_path)

        store['load_result'] = resulting_node.name()
