# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os
import clique

from pyffmpeg import FFmpeg

from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class HarmonyMovieExporterPlugin(BasePlugin):
    name = 'harmony_movie_exporter'

    def run(self, store):
        '''
        Pick up previously rendered image sequence and transcode it to a movie file, storing the path
        in the *store* under the component name.
        '''
        component_name = self.options.get('component')
        sequence_expression = (
            store['components'].get('sequence', {}).get('exported_path')
        )
        if not sequence_expression:
            raise PluginExecutionError(
                f'Could not locate previously exported image sequence component and output'
            )

        ff = FFmpeg()

        exported_path = get_temp_path(filename_extension='mp4')

        collection = clique.parse(sequence_expression)
        if not collection:
            raise PluginExecutionError(
                message=f"Could not parse image sequence from: {sequence_expression}"
            )

        # Get the path from collection
        sequence_path = collection.format('{head}{padding}{tail}')

        self.logger.info(
            f'Transcoding {sequence_path} > {exported_path} using ffmpeg({ff._ffmpeg_file})'
        )

        if not ff.options(
            f'-framerate 24 -i "{sequence_path}" -c:v libx264 -pix_fmt yuv420p {exported_path}'
        ):
            raise PluginExecutionError(
                f'Failed to transcode {sequence_path} > {exported_path} using ffmpeg!'
            )

        if (
            not os.path.exists(exported_path)
            or os.path.getsize(exported_path) == 0
        ):
            raise PluginExecutionError(
                f'Could not locate rendered movie or zero size: {exported_path}'
            )

        store['components'][component_name]['exported_path'] = exported_path
