# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import hou

from ftrack_connect_pipeline_houdini import plugin
from ftrack_connect_pipeline_houdini.constants import asset as asset_const
import ftrack_api


class HoudiniFBXLoaderImporterPlugin(plugin.HoudiniLoaderImporterPlugin):
    plugin_name = 'houdini_fbx_loader_importer'

    def run(self, context_data=None, data=None, options=None):
        '''Load FBX geometry into Houdini from collected paths provided with *data* based on *options*'''

        results = {}
        paths_to_import = []
        for collector in data:
            paths_to_import.append(
                collector['result'].get(asset_const.COMPONENT_PATH)
            )
        for component_path in paths_to_import:
            self.logger.debug('Importing path {}'.format(component_path))

            (node, import_messages) = hou.hipFile.importFBX(component_path)
            self.logger.debug(
                'FBX import messages: {}'.format(import_messages)
            )

            results[component_path] = node.path()

        return results


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = HoudiniFBXLoaderImporterPlugin(api_object)
    plugin.register()
