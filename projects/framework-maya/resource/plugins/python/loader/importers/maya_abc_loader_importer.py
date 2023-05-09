# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import maya.cmds as cmds

from ftrack_connect_pipeline_maya import plugin
from ftrack_connect_pipeline_maya.constants import asset as asset_const
import ftrack_api


class MayaAbcLoaderImporterPlugin(plugin.MayaLoaderImporterPlugin):
    '''Maya Alembic importer plugin'''

    plugin_name = 'maya_abc_loader_importer'

    def run(self, context_data=None, data=None, options=None):
        '''Load alembic files pointed out by collected paths supplied in *data*'''

        # ensure to load the alembic plugin
        cmds.loadPlugin('AbcImport.so', qt=1)

        results = {}

        paths_to_import = []
        for collector in data:
            paths_to_import.append(
                collector['result'].get(asset_const.COMPONENT_PATH)
            )

        for component_path in paths_to_import:
            self.logger.debug('Importing path {}'.format(component_path))
            import_result = cmds.AbcImport(component_path)
            results[component_path] = import_result

        return results


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MayaAbcLoaderImporterPlugin(api_object)
    plugin.register()
