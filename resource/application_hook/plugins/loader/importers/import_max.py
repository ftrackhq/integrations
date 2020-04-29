# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import MaxPlus

from ftrack_connect_pipeline_3dsmax import plugin


class ImportMayaPlugin(plugin.LoaderImporterMaxPlugin):
    plugin_name = 'import_max'

    def run(self, context=None, data=None, options=None):
        results = {}
        paths_to_import = data
        for component_path in paths_to_import:
            self.logger.debug('Importing path {}'.format(component_path))
            fm = MaxPlus.FileManager
            import_result =fm.Open(component_path, True, True, True, False)
            results[component_path] = import_result

        return results


def register(api_object, **kw):
    plugin = ImportMayaPlugin(api_object)
    plugin.register()