# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import ftrack_api

from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_nuke.constants.asset import modes as load_const


class ImportNukePlugin(plugin.LoaderImporterNukePlugin):
    plugin_name = 'load_nuke'

    load_modes = load_const.LOAD_MODES

    def _get_nuke_options(self, load_options):
        self.logger.debug("No options implemented")
        nuke_options = {}

        return nuke_options

    def run(self, context=None, data=None, options=None):
        load_mode = options.get('load_mode', self.load_modes.keys()[0])
        load_options = options.get('load_options', {})
        load_mode_fn = self.load_modes.get(load_mode, self.load_modes.keys()[0])

        nuke_options = {}
        if load_options:
            nuke_options = self._get_nuke_options(load_options)

        results = {}
        paths_to_import = data
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
    plugin = ImportNukePlugin(api_object)
    plugin.register()
