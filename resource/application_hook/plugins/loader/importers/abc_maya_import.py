# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import maya.cmds as cmd

from ftrack_connect_pipeline_maya import plugin


class AbcMayaImportPlugin(plugin.ImporterMayaPlugin):
    plugin_name = 'abc_maya_import'

    def run(self, context=None, data=None, options=None):
        # ensure to load the alembic plugin
        cmd.loadPlugin('AbcExport.so', qt=1)

        results = {}
        paths_to_import = data
        for component_path in paths_to_import:
            self.logger.debug('Importing path {}'.format(component_path))
            import_result = cmd.AbcImport(component_path)
            results[component_path] = import_result

        print "results --> {}".format(results)
        return results


def register(api_object, **kw):
    plugin = AbcMayaImportPlugin(api_object)
    plugin.register()