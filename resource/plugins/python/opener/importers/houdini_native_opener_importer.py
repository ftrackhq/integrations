# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline_houdini import plugin
from ftrack_connect_pipeline_houdini.constants.asset import modes as load_const
from ftrack_connect_pipeline_houdini.constants import asset as asset_const
import ftrack_api


class HoudiniNativeOpenerImporterPlugin(plugin.HoudiniOpenerImporterPlugin):
    plugin_name = 'houdini_native_opener_importer'

    def run(self, context_data=None, data=None, options=None):
        '''Open Houdini based on collected path provided in *data*'''

        load_mode = load_const.OPEN_MODE
        load_mode_fn = self.load_modes.get(load_mode)

        houdini_options = {}

        results = {}

        paths_to_import = []
        for collector in data:
            paths_to_import.append(
                collector['result'].get(asset_const.COMPONENT_PATH)
            )

        for component_path in paths_to_import:
            self.logger.debug('Opening path {}'.format(component_path))

            load_result = load_mode_fn(component_path, houdini_options)

            results[component_path] = load_result

        return results


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = HoudiniNativeOpenerImporterPlugin(api_object)
    plugin.register()
