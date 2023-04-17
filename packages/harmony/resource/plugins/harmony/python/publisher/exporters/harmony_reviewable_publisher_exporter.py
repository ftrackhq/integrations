# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import tempfile
import os

from pyffmpeg import FFmpeg

from ftrack_connect_pipeline_harmony import utils as harmony_utils

from ftrack_connect_pipeline_harmony import plugin
import ftrack_api


class HarmonyReviewablePublisherExporterPlugin(
    plugin.HarmonyPublisherExporterPlugin
):
    plugin_name = 'harmony_reviewable_publisher_exporter'

    def run(self, context_data=None, data=None, options=None):
        '''Export a Harmony reviewable out of the rendered image sequence, using ffmpeg'''

        full_path = tempfile.NamedTemporaryFile(
            delete=False, suffix='.mp4'
        ).name

        destination_path, extension = harmony_utils.get_image_sequence_path()

        os.chdir(destination_path)

        ff = FFmpeg()

        self.logger.info(
            'Transcoding {}*{} > {} using ffmpeg...'.format(
                destination_path, extension, full_path
            )
        )

        if not ff.options(
            "-framerate 24 -pattern_type glob -i '*{}' -c:v libx264 -pix_fmt yuv420p {}".format(
                extension, full_path
            )
        ):
            return False, {
                'message': 'Failed to transcode {} > {} using ffmpeg!'.format(
                    destination_path, full_path
                )
            }

        return [full_path]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = HarmonyReviewablePublisherExporterPlugin(api_object)
    plugin.register()
