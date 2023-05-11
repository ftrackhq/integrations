# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import os

import hou

from ftrack_connect_pipeline_houdini import plugin
from ftrack_connect_pipeline_houdini.constants import asset as asset_const
import ftrack_api


class HoudiniAbcImportPlugin(plugin.HoudiniLoaderImporterPlugin):
    plugin_name = 'houdini_abc_loader_importer'

    def bake_camera_animation(self, node, frameRange):
        '''Bake camera to World Space'''
        bake_node = hou.node('/obj').createNode('cam', '%s_bake' % node.name())

        for x in ['resx', 'resy']:
            bake_node.parm(x).set(node.parm(x).eval())

        for frame in range(
            int(float(frameRange[0])), (int(float(frameRange[1])) + 1)
        ):
            time = (frame - 1) / hou.fps()
            matrix = node.worldTransformAtTime(time).explode()

            for parm in matrix:
                if 'shear' not in parm:
                    for x, p in enumerate(bake_node.parmTuple(parm[0])):
                        p.setKeyframe(hou.Keyframe(matrix[parm][x], time))

        return bake_node

    def run(self, context_data=None, data=None, options=None):
        '''Load alembic geometry into Houdini from collected paths provided with *data* based on *options*'''
        results = {}
        paths_to_import = []
        for collector in data:
            paths_to_import.append(
                collector['result'].get(asset_const.COMPONENT_PATH)
            )
        for component_path in paths_to_import:
            self.logger.debug('Importing path {}'.format(component_path))

            node = hou.node('/obj').createNode(
                'alembicarchive', context_data['asset_name']
            )
            node.parm('buildSubnet').set(False)
            node.parm('fileName').set(component_path)
            hou.hscript('opparm -C {0} buildHierarchy (1)'.format(node.path()))
            node.moveToGoodPosition()

            if context_data['asset_type_name'] == 'cam':
                # Bake the camera
                for obj in node.glob('*'):
                    if 'cam' in obj.type().name().lower():
                        self.logger.debug('Baking camera {}'.format(obj))
                        bcam = self.bake_camera_animation(
                            obj, [os.getenv('FS'), os.getenv('FE')]
                        )
                        node.destroy()
                        node = bcam
                        break

            results[component_path] = node.path()

        return results


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = HoudiniAbcImportPlugin(api_object)
    plugin.register()
