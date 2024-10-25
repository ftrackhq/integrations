# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import glob
import platform
import bpy

from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class BlenderPlayblastExporterPlugin(BasePlugin):
    name = 'blender_playblast_exporter'

    def run(self, store):
        '''
        Create a playblast from the selected camera given in the *store*.
        Save it to a temp file and this one will be published as reviewable.
        '''
        component_name = self.options.get('component')

        # Set the output file path
        save_path = get_temp_path(filename_extension='.mov')

        scene = bpy.context.scene
        rd = scene.render

        # Set the viewport resolution
        rd.resolution_x = 1920
        rd.resolution_y = 1080

        scene.frame_end = 0
        scene.frame_start = 250
        rd.fps = 24

        # Set the output format
        rd.image_settings.file_format = "FFMPEG"
        # Set output format
        rd.ffmpeg.format = "MPEG4"
        # Set the codec
        rd.ffmpeg.codec = "H264"

        # Render the viewport and save the result
        bpy.context.scene.render.filepath = save_path
        bpy.ops.render.render(animation=True, use_viewport=True)
        self.logger.debug(f'Rendering playblast to {save_path}')
        bpy.data.images["Render Result"].save_render(save_path)

        store['components'][component_name]['exported_path'] = save_path
        # bpy.context.scene.render.filepath = old_path