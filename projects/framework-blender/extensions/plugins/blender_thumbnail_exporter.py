# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import bpy

from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError
from ftrack_framework_blender.utils import blender_operator


class BlenderThumbnailExporterPlugin(BasePlugin):
    name = 'blender_thumbnail_exporter'

    @blender_operator
    def blender_ops(self, exported_path):
        bpy.context.scene.render.image_settings.file_format = "JPEG"
        bpy.context.scene.render.filepath = exported_path

        bpy.ops.render.opengl(
            animation=False, write_still=True, view_context=True
        )

    @blender_operator
    def blender_undo(self):
        bpy.ops.ed.undo()

    def run(self, store):
        '''
        Create a screenshot from the selected camera given in the *store*.
        Save it to a temp file and this one will be published as thumbnail.
        '''

        component_name = self.options.get('component')
        exported_path = get_temp_path(filename_extension='.jpg')
        self.logger.debug(f'Rendering thumbnail to {exported_path}')

        try:
            self.blender_ops(exported_path)
            store['components'][component_name][
                'exported_path'
            ] = exported_path
        except Exception as error:
            raise PluginExecutionError(
                f"Error trying to create the thumbnail, error: {error}"
            )
        # finally:
        #     # bpy.ops.ed.undo()
        #     self.blender_undo()
