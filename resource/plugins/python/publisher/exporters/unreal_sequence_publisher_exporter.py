# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os

import unreal

import ftrack_api

from ftrack_connect_pipeline_unreal import utils as unreal_utils
from ftrack_connect_pipeline_unreal import plugin


class UnrealSequencePublisherExporterPlugin(
    plugin.UnrealPublisherExporterPlugin
):
    '''Unreal image sequence exporter plugin'''

    plugin_name = 'unreal_sequence_publisher_exporter'

    _standard_structure = ftrack_api.structure.standard.StandardStructure()

    def run(self, context_data=None, data=None, options=None):
        '''Pick up an existing file image sequence, or render images from level sequence, given
        in *data* with the given *options*.'''

        media_path = None
        render_path = None
        level_sequence_name = None
        for collector in data:
            for result in collector['result']:
                for key, value in result.items():
                    if key == 'media_path':
                        media_path = value
                    elif key == 'render_path':
                        render_path = value
                    elif key == 'level_sequence_name':
                        level_sequence_name = value

        if not media_path:
            # Find level sequence
            level_sequence = None

            all_sequences = unreal_utils.get_all_sequences(as_names=False)

            for seq in all_sequences:
                if (
                    seq.get_name() == level_sequence_name
                    or level_sequence_name.startswith(
                        '{}_'.format(seq.get_name())
                    )
                ):
                    level_sequence = seq
                    break

            if not level_sequence:
                return False, {
                    'message': 'Level sequence "{}" not found, please refresh publisher!'.format(
                        level_sequence_name
                    )
                }

            # Determine render destination path
            if not render_path or not os.path.exists(render_path):
                render_path_base = os.path.join(
                    unreal.SystemLibrary.get_project_saved_directory(),
                    'VideoCaptures',
                    level_sequence_name,
                )
                next_version = 0
                while True:
                    render_path = os.path.join(
                        render_path_base, 'v{}'.format(next_version)
                    )
                    if not os.path.exists(render_path):
                        break
                    next_version += 1
            self.logger.info(
                'Rendering image sequence to folder: {}'.format(render_path)
            )

            unreal_map = unreal.EditorLevelLibrary.get_editor_world()
            unreal_map_path = unreal_map.get_path_name()
            unreal_sequence_path = level_sequence.get_path_name()

            asset_name = self._standard_structure.sanitise_for_filesystem(
                context_data['asset_name']
            )

            file_format = options.get('file_format', 'exr')
            result = self.render(
                unreal_sequence_path,
                unreal_map_path,
                asset_name,
                render_path,
                level_sequence.get_display_rate().numerator,
                self.compile_capture_args(options),
                self.logger,
                image_format=file_format,
            )

            if isinstance(result, tuple):
                return result

            path = result

            # try to get start and end frames from sequence
            # control for test publish(subset of sequence)
            frame_start = level_sequence.get_playback_start()
            frame_end = level_sequence.get_playback_end() - 1
            base_file_path = (
                path[:-12]
                if path.endswith('.{frame}.%s' % file_format)
                else path
            )

            media_path = '{0}.%04d.{1} [{2}-{3}]'.format(
                base_file_path, file_format, frame_start, frame_end
            )

        return [media_path]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    output_plugin = UnrealSequencePublisherExporterPlugin(api_object)
    output_plugin.register()
