# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os
import clique
import tempfile
import shutil

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

        collected_objects = []
        have_media_path = False
        render_path = None
        for collector in data:
            for result in collector['result']:
                for key, value in result.items():
                    if key == 'media_path':
                        have_media_path = True
                        collected_objects.append(value)
                    elif key == 'render_path':
                        render_path = value
                    elif key == 'level_sequence_name':
                        collected_objects.append(value)

        if have_media_path:

            media_path = collected_objects[0]

            collections = clique.parse(media_path)

            self.logger.debug(
                'Using pre-rendered file sequence path: "{}", copying to temp.'.format(
                    media_path
                )
            )

            temp_sequence_dir = tempfile.mkdtemp()
            if not os.path.exists(temp_sequence_dir):
                os.makedirs(temp_sequence_dir)

            # Copy sequence
            for collection in collections:
                source_path = str(collection)
                destination_path = os.path.join(
                    temp_sequence_dir, os.path.basename(source_path)
                )
                self.logger.debug(
                    'Copying "{}" > "{}"'.format(source_path, destination_path)
                )
                shutil.copy(source_path, destination_path)

            new_file_path = '{}'.format(
                os.path.join(
                    temp_sequence_dir,
                    os.path.basename(media_path),
                )
            )

        else:
            # Find level sequence
            level_sequence = None

            seq_name = None
            all_sequences = unreal_utils.get_all_sequences(as_names=False)
            for _seq_name in collected_objects:
                seq_name = _seq_name
                for seq in all_sequences:
                    if seq.get_name() == _seq_name or _seq_name.startswith(
                        '{}_'.format(seq.get_name())
                    ):
                        level_sequence = seq
                        break
                if level_sequence:
                    break

            if level_sequence is None:
                return False, {
                    'message': 'Level sequence "{}" not found, please refresh publisher!'.format(
                        seq_name
                    )
                }

            # Determine render destination path
            if render_path is None or not os.path.exists(render_path):
                render_path_base = os.path.join(
                    unreal.SystemLibrary.get_project_saved_directory(),
                    'VideoCaptures',
                    seq_name,
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

            new_file_path = '{0}.%04d.{1} [{2}-{3}]'.format(
                base_file_path, file_format, frame_start, frame_end
            )

        return [new_file_path]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    output_plugin = UnrealSequencePublisherExporterPlugin(api_object)
    output_plugin.register()
