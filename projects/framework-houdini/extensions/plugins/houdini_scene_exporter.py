# :coding: utf-8
# :copyright: Copyright (c) 2014-2024 ftrack

import os
import subprocess

import hou

from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class HoudiniSceneExporterPlugin(BasePlugin):
    name = 'houdini_scene_exporter'

    def run(self, store):
        '''
        If export type is selection then export the selection objects in the
        scene with the options passed. Otherwise, set the current scene path to
        the store.
        '''
        component_name = self.options.get('component')

        export_type = store['components'][component_name].get('export_type')

        scene_path = store['components'][component_name].get('scene_path')

        if export_type == 'selection':
            try:
                save_path = get_temp_path(filename_extension='hip')

                selected_objects = hou.selectedNodes()
                obj_path = hou.node('/obj')
                geometry_objects = obj_path.glob('*')
                collected_objects = []
                for obj in selected_objects:
                    if obj in geometry_objects:
                        collected_objects.append(obj.path())

                hou.copyNodesToClipboard(
                    [hou.node(obj_path) for obj_path in collected_objects]
                )

                command = "hou.pasteNodesFromClipboard(hou.node('/obj'));\
                    hou.hipFile.save('{}')".format(
                    save_path.replace("\\", "\\\\")
                )

                cmd = [
                    os.path.join(os.getenv('HFS'), 'bin', 'hython'),
                    '-c',
                    command,
                ]

                my_env = os.environ.copy()
                if 'HOUDINI_PATH' in my_env:
                    del my_env['HOUDINI_PATH']

                if subprocess.Popen(cmd, env=my_env).wait() != 0:
                    return False, {'message': 'Node export failed!'}

                exported_path = save_path
            except Exception as error:
                raise PluginExecutionError(
                    message=f"Couldn't export selection, error:{error}"
                )

        else:
            exported_path = scene_path

        store['components'][component_name]['exported_path'] = exported_path
