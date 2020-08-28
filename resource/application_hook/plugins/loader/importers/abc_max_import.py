# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import ftrack_api

from ftrack_connect_pipeline_3dsmax import plugin
from ftrack_connect_pipeline_3dsmax.utils import max_alembic_commands as abc_utils


class ImportAbcMaxPlugin(plugin.LoaderImporterMaxPlugin):
    plugin_name = 'import_max_abc'

    def run(self, context=None, data=None, options=None):
        results = {}
        paths_to_import = data
        # for component_path in paths_to_import:
        #     result = None
        #     try:
        #         result = abc_utils.import_abc(component_path, options)
        #     except RuntimeError, e:
        #         self.logger.error(str(e))
        #     results[component_path] = result

        return results

def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = ImportAbcMaxPlugin(api_object)
    plugin.register()