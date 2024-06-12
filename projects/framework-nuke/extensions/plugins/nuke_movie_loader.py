# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import nuke

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class NukeMovieLoaderPlugin(BasePlugin):
    '''Load a movie into Nuke'''

    name = 'nuke_movie_loader'

    def run(self, store):
        '''
        Expects the movie to load in the :obj:`self.options`, loads the movie
        '''
        movie_path = store.get('component_path')
        if not movie_path:
            raise PluginExecutionError(f'No movie path provided in store!')

        n = nuke.nodes.Read()
        n['file'].fromUserText(movie_path)

        self.logger.debug(f'Created movie read node, reading: {movie_path}')
