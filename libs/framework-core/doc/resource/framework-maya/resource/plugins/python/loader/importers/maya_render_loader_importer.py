# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import maya.cmds as cmds

from ftrack_framework_maya import plugin
import ftrack_api


class MayaRenderLoaderImporterPlugin(plugin.MayaLoaderImporterPlugin):
    '''Maya Quicktime importer plugin'''

    plugin_name = 'maya_render_loader_importer'

    def run(self, context_data=None, data=None, options=None):
        '''Load alembic files pointed out by collected paths supplied in *data*'''

        results = {}

        camera_name = options.get('camera_name', 'persp')
        paths_to_import = []
        for collector in data:
            paths_to_import.extend(collector['result'])

        for component_path in paths_to_import:
            self.logger.debug(
                'Importing path "{}" as image plane to camera "{}"'.format(
                    component_path, camera_name
                )
            )
            imagePlane = cmds.imagePlane(
                camera=camera_name, fileName=component_path
            )
            cmds.setAttr('{}.type'.format(imagePlane[0]), 2)
            cmds.setAttr('{}.useFrameExtension'.format(imagePlane[0]), True)

            self.logger.info(
                'Imported "{}" to {}.'.format(component_path, imagePlane[0])
            )

            results[component_path] = imagePlane[0]

        return results


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MayaRenderLoaderImporterPlugin(api_object)
    plugin.register()
