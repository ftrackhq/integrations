# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import glob
import bpy

from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class BlenderThumbnailExporterPlugin(BasePlugin):
    name = 'blender_thumbnail_exporter'

    def run(self, store):
        '''
        Create a screenshot from the selected camera given in the *store*.
        Save it to a temp file and this one will be published as thumbnail.
        '''
        old_path = bpy.context.scene.render.filepath

        component_name = self.options.get('component')
        exported_path = get_temp_path(filename_extension='png')
        # store blender output path
        try:
            bpy.context.scene.render.filepath = exported_path
            bpy.ops.render.opengl(animation=False, write_still=True)

        except Exception as error:
            raise PluginExecutionError(
                f"Error trying to create the thumbnail, error: {error}"
            )
        # restore old blender path
        bpy.context.scene.render.filepath = old_path
        store['components'][component_name]['exported_path'] = exported_path
