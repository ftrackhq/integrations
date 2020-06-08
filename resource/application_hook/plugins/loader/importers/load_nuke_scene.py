# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_nuke.constants import asset as asset_const
from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils

import nuke


class ImportNukePlugin(plugin.LoaderImporterNukePlugin):
    plugin_name = 'load_nuke'

    load_modes = {
        asset_const.OPEN_MODE: nuke_utils.open_scene,
        asset_const.IMPORT_MODE: nuke_utils.import_scene,
        asset_const.REFERENCE_MODE: nuke_utils.reference_scene,
    }

    def _get_nuke_options(self, load_options):
        self.logger.debug("No options implemented")
        return {}

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
            if load_mode != asset_const.OPEN_MODE:
                self.logger.info("setting it with name")
                results[component_path] = load_result.name()
            else:
                self.logger.info("setting it with no name")
                results[component_path] = load_result

        return results


def register(api_object, **kw):
    plugin = ImportNukePlugin(api_object)
    plugin.register()
