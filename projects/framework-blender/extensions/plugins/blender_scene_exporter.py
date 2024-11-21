# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import bpy
from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class BlenderSceneExporterPlugin(BasePlugin):
    name = 'blender_scene_exporter'

    def run(self, store):
        '''
        If export type is selection then export the selection objects in the
        scene with the options passed. Otherwise, set the current scene path to
        the store.
        '''

        component_name = self.options.get('component')
        export_type = store['components'][component_name].get('export_type')
        exported_path = store['components'][component_name].get('scene_name')

        try:
            # Save file to a temp file
            if export_type == 'selection':
                exported_path = get_temp_path(filename_extension='.blend')

                # open the undo group
                bpy.ops.ed.undo_push()

                internal_scene_name = bpy.context.scene.name
                bpy.context.scene.name = f"{internal_scene_name}_temp"

                objects = bpy.context.selected_objects
                export_scene = bpy.data.scenes.new(internal_scene_name)
                for ob in objects:
                    export_scene.collection.objects.link(ob)

                bpy.context.window.scene = export_scene

                for scn in bpy.data.scenes:
                    if scn != export_scene:
                        bpy.data.scenes.remove(scn)

                bpy.data.orphans_purge(do_recursive=True)
                bpy.ops.wm.save_as_mainfile(filepath=exported_path, copy=True)

                bpy.ops.ed.undo()

            store['components'][component_name]['exported_path'] = exported_path

        except Exception as error:
            raise PluginExecutionError(
                message=f"Couldn't export scene to {exported_path} due to error:{error}"
            )

