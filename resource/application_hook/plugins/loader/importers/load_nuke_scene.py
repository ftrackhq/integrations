# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import nuke

from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_nuke.constants import asset as asset_const
from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils


class ImportNukePlugin(plugin.LoaderImporterNukePlugin):
    plugin_name = 'import_nuke'

    def run(self, context=None, data=None, options=None):
        #Add options import, open, reference
        results = {}
        paths_to_import = data
        load_mode = options.get('load_mode', asset_const.OPEN_MODE)
        results['asset_load_mode'] = load_mode
        import_modes = {
            asset_const.OPEN_MODE: nuke.scriptOpen,
            asset_const.IMPORT_MODE: nuke.nodePaste,
            asset_const.REFERENCE_MODE: nuke_utils.reference_scene,
        }
        import_mode_fn = import_modes.get(load_mode, nuke.scriptOpen)
        for component_path in paths_to_import:
            load_result = None
            self.logger.debug('Loading path {}'.format(component_path))
            load_result = import_mode_fn(component_path)
            if load_mode != asset_const.OPEN_MODE:
                results[component_path] = load_result.name()
            else:
                results[component_path] = load_result

        return results


def register(api_object, **kw):
    plugin = ImportNukePlugin(api_object)
    plugin.register()