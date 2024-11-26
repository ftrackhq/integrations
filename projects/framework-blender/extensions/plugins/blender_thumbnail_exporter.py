# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

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

        component_name = self.options.get('component')
        exported_path = get_temp_path(filename_extension='.jpg')
        self.logger.debug(f'Rendering thumbnail to {exported_path}')

        file_format = bpy.context.scene.render.image_settings.file_format
        file_path = bpy.context.scene.render.filepath
        context = bpy.context
        blender_context_copy = bpy.context.copy()
        store_context = store['components']['snapshot']['blender_context_copy']
        if blender_context_copy != store_context:
            self.logger.warning(
                "Context are different: {} \n \n sotre context: {}".format(
                    blender_context_copy, store_context
                )
            )

        def get_context(type):
            for screen in bpy.data.screens:
                print(f"screen: {screen}")
                for area in screen.areas:
                    print(f"area: {area}")
                    print(f"area.type: {area.type}")
                    if area.type == type:
                        context_override = {"area": area, "screen": screen}
                        return context_override

        override = get_context("VIEW_3D")
        print(f"override: {override}")

        try:
            bpy.context.scene.render.image_settings.file_format = "JPEG"
            bpy.context.scene.render.filepath = exported_path

            with bpy.context.temp_override(**override):
                bpy.ops.render.opengl(
                    animation=False, write_still=True, view_context=True
                )
        except Exception as error:
            raise PluginExecutionError(
                f"Error trying to create the thumbnail, error: {error}"
            )
        finally:
            bpy.context.scene.render.image_settings.file_format = file_format
            bpy.context.scene.render.filepath = file_path

        store['components'][component_name]['exported_path'] = exported_path
