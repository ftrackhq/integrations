# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os
import tempfile
import shutil

import unreal

import ftrack_api

from ftrack_connect_pipeline_unreal import plugin
from ftrack_connect_pipeline_unreal import utils as unreal_utils


class UnrealReviewablePublisherExporterPlugin(
    plugin.UnrealPublisherExporterPlugin
):
    '''Unreal reviewable exporter plugin'''

    plugin_name = 'unreal_reviewable_publisher_exporter'

    _standard_structure = ftrack_api.structure.standard.StandardStructure()

    def run(self, context_data=None, data=None, options=None):
        '''Pick up an existing movie, or render a movie from level sequence, given
        in *data* with the given *options*.'''

        movie_path = None
        render_path = None
        mode = 'render'
        for collector in data:
            for result in collector['result']:
                for key, value in result.items():
                    if key == 'mode':
                        mode = value
                    if key == 'movie_path':
                        movie_path = value
                        break
                    if key == 'render_path':
                        render_path = value
        if mode == 'pickup' and not movie_path:
            mode = 'render'
        if mode == 'render' and not render_path:
            render_path = unreal_utils.get_project_settings().get('image_sequence_path')
            if not render_path:
                self.logger.debug(
                    'Can not find selected image sequence'
                )
                return False

        if render_path:
            # TODO: convert image sequence to movie file.
            pass

        self.logger.debug(
            'Using pre-rendered movie path: "{}", copying to temp.'.format(
                movie_path
            )
        )

        temp_movie_path = tempfile.NamedTemporaryFile(
            delete=False, suffix='.mov'
        ).name

        shutil.copy(movie_path, temp_movie_path)

        return [temp_movie_path]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UnrealReviewablePublisherExporterPlugin(api_object)
    plugin.register()
