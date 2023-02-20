# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import ftrack_api

from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_nuke.constants.asset import modes as load_const
from ftrack_connect_pipeline_nuke.constants import asset as asset_const


class NukeNativeLoaderImporterPlugin(plugin.NukeLoaderImporterPlugin):
    '''Nuke native script loader plugin'''

    plugin_name = 'nuke_native_loader_importer'

    load_modes = load_const.LOAD_MODES

    def _get_nuke_options(self, load_options):
        self.logger.debug("No options implemented")
        nuke_options = {}

        return nuke_options

    def run(self, context_data=None, data=None, options=None):
        '''Load collected Nuke script(s) supplied with *data*'''

        load_mode = options.get('load_mode', list(self.load_modes.keys())[0])
        load_options = options.get('load_options', {})
        load_mode_fn = self.load_modes.get(
            load_mode, list(self.load_modes.keys())[0]
        )

        nuke_options = {}
        if load_options:
            nuke_options = self._get_nuke_options(load_options)

        results = {}

        paths_to_import = []
        for collector in data:
            paths_to_import.append(
                collector['result'].get(asset_const.COMPONENT_PATH)
            )

        for component_path in paths_to_import:
            self.logger.debug('Loading path {}'.format(component_path))

            load_result = load_mode_fn(component_path, nuke_options)
            if load_mode != load_const.OPEN_MODE:
                results[component_path] = load_result.name()
            else:
                results[component_path] = load_result

        return results


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeNativeLoaderImporterPlugin(api_object)
    plugin.register()
