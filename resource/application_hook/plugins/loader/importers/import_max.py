# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline_3dsmax import plugin
from ftrack_connect_pipeline_3dsmax.constants import asset as asset_const
from ftrack_connect_pipeline_3dsmax.utils import custom_commands as max_utils


class ImportMayaPlugin(plugin.LoaderImporterMaxPlugin):
    plugin_name = 'import_max'

    def run(self, context=None, data=None, options=None):
        results = {}
        paths_to_import = data
        load_mode = options.get('load_mode', asset_const.OPEN_MODE)
        results['asset_load_mode'] = load_mode
        import_modes = {
            asset_const.OPEN_MODE: max_utils.open_scene,
            asset_const.IMPORT_MODE: max_utils.merge_max_file,
            asset_const.SCENE_XREF_MODE: max_utils.import_scene_XRef,
            asset_const.OBJECT_XREF_MODE: max_utils.import_obj_XRefs,
        }
        import_mode_fn = import_modes.get(load_mode, max_utils.open_scene)
        for component_path in paths_to_import:
            load_result = None
            self.logger.debug('Loading path {}'.format(component_path))
            import_mode_fn(component_path)

            results[component_path] = load_result

        return results


def register(api_object, **kw):
    plugin = ImportMayaPlugin(api_object)
    plugin.register()