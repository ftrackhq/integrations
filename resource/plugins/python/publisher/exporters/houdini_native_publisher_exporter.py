# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

import tempfile
import os
import subprocess

import hou

from ftrack_connect_pipeline_houdini import plugin
import ftrack_api


class HoudiniNativePublisherExporterPlugin(
    plugin.HoudiniPublisherExporterPlugin
):
    plugin_name = 'houdini_native_publisher_exporter'

    extension = '.hip'
    filetype = 'hip'

    def run(self, context_data=None, data=None, options=None):
        '''Export collected object paths provided with *data* to a Houdini files'''

        new_file_path = tempfile.NamedTemporaryFile(
            delete=False, suffix=self.extension
        ).name

        collected_objects = []
        is_scene_publish = False
        for collector in data:
            collected_objects.extend(collector['result'])
            if collector.get('options', {}).get('export') == 'scene':
                is_scene_publish = True

        if is_scene_publish:
            # Export entire scene
            scene_name_orig = hou.hipFile.path()
            hou.hipFile.save(new_file_path, save_to_recent_files=False)
            hou.hipFile.setName(scene_name_orig)
        else:
            # Export selected
            hou.copyNodesToClipboard(
                [hou.node(obj_path) for obj_path in collected_objects]
            )

            command = "hou.pasteNodesFromClipboard(hou.node('/obj'));\
                            hou.hipFile.save('{}')".format(
                new_file_path.replace("\\", "\\\\")
            )

            cmd = [
                os.path.join(os.getenv('HFS'), 'bin', 'hython'),
                '-c',
                command,
            ]

            my_env = os.environ.copy()
            if 'HOUDINI_PATH' in my_env:
                del my_env['HOUDINI_PATH']

            self.logger.debug(
                'Exporting nodes {} with command: "{}".'.format(
                    collected_objects, cmd
                )
            )

            if subprocess.Popen(cmd, env=my_env).wait() != 0:
                return False, {'message': 'Node export failed!'}

        return [new_file_path]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    scene_plugin = HoudiniNativePublisherExporterPlugin(api_object)
    scene_plugin.register()
