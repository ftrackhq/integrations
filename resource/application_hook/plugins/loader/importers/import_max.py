# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline_3dsmax import plugin
from ftrack_connect_pipeline_3dsmax import constants
from ftrack_connect_pipeline_3dsmax.utils import custom_commands as max_utils


class ImportMayaPlugin(plugin.LoaderImporterMaxPlugin):
    plugin_name = 'import_max'

    def run(self, context=None, data=None, options=None):
        results = {}
        paths_to_import = data
        load_mode = options.get('load_mode', constants.OPEN_MODE)
        results['asset_load_mode'] = load_mode
        for component_path in paths_to_import:
            load_result = None
            self.logger.debug('Loading path {}'.format(component_path))
            if load_mode == constants.OPEN_MODE:
                load_result = max_utils.open_scene(component_path)
            elif load_mode == constants.IMPORT_MODE:
                load_result = max_utils.merge_max_file(component_path)
            elif load_mode == constants.SCENE_XREF_MODE:
                load_result = max_utils.import_scene_XRef(component_path)
            elif load_mode == constants.OBJECT_XREF_MODE:
                load_result = max_utils.import_obj_XRefs(component_path)

            results[component_path] = load_result

        return results


def register(api_object, **kw):
    plugin = ImportMayaPlugin(api_object)
    plugin.register()