# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import maya.cmds as cmd

from ftrack_connect_pipeline_maya import plugin
from ftrack_connect_pipeline import constants


class ImportMayaPlugin(plugin.LoaderImporterMayaPlugin):
    plugin_name = 'import_maya'

    def run(self, context=None, data=None, options=None):
        #Add options import, open, reference
        results = {}
        paths_to_import = data
        for component_path in paths_to_import:
            self.logger.debug('Importing path {}'.format(component_path))
            import_result = cmd.file(component_path, i=True)
            results[component_path] = import_result

        return results


def register(api_object, **kw):
    plugin = ImportMayaPlugin(api_object)
    plugin.register()