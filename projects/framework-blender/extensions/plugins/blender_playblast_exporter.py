# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import bpy

from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError
from ftrack_framework_blender.utils import blender_operator


class BlenderPlayblastExporterPlugin(BasePlugin):
    name = 'blender_playblast_exporter'

    @blender_operator
    def blender_ops(self, save_path, camera_name):
        rd = bpy.context.scene.render

        camera = [
            obj
            for obj in bpy.data.objects
            if obj.type == 'CAMERA' and obj.name == camera_name
        ][0]

        bpy.context.scene.camera = camera

        # Set the viewport resolution
        rd.resolution_x = 1920
        rd.resolution_y = 1080

        # Set the output format
        rd.image_settings.file_format = "FFMPEG"
        # Set output format
        rd.ffmpeg.format = "MPEG4"
        # Set the codec
        rd.ffmpeg.codec = "H264"

        # Render the viewport and save the result
        bpy.context.scene.render.filepath = save_path
        self.logger.debug(f'Rendering playblast to {save_path}')

        bpy.ops.render.render(
            animation=True, use_viewport=False, write_still=True
        )

    def run(self, store):
        '''
        Create a playblast from the selected camera given in the *store*.
        Save it to a temp file and this one will be published as reviewable.
        '''
        component_name = self.options.get('component')

        # Set the output file path
        save_path = get_temp_path(filename_extension='.mp4')
        camera_name = store['components'][component_name]['camera_name']

        try:
            self.blender_ops(save_path, camera_name)
            store['components'][component_name]['exported_path'] = save_path

        except Exception as error:
            raise PluginExecutionError(
                message=f"Couldn't export playblast to {save_path} due to error:{error}"
            )
