# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import nuke

from ftrack_connect_pipeline_nuke import plugin


class ImportNukePlugin(plugin.LoaderImporterNukePlugin):
    plugin_name = 'import_nuke'

    def run(self, context=None, data=None, options=None):
        #Add options import, open, reference
        results = {}
        paths_to_import = data
        for component_path in paths_to_import:
            self.logger.debug('Importing path {}'.format(component_path))
            import_result = nuke.scriptOpen(component_path)
            results[component_path] = import_result

        return results


def register(api_object, **kw):
    plugin = ImportNukePlugin(api_object)
    plugin.register()