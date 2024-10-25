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
        scene_name = store['components'][component_name].get('scene_name')

        try:
            # Save file to a temp file
            exported_path = get_temp_path(
                filename_extension='.blend'
            )
            bpy.ops.wm.save_as_mainfile(filepath=exported_path)
            self.logger.debug(f'Saving blender snapshot to {exported_path}')

            self.logger.debug(
                f"Selected objects exported to: {exported_path}."
            )
            store['components'][component_name]['exported_path'] = exported_path

        except Exception as error:
            raise PluginExecutionError(
                message=f"Couldn't export selection, error:{error}"
            )
