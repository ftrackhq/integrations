# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline_3dsmax import plugin
from ftrack_connect_pipeline_3dsmax.constants.asset import modes as load_const


class LoadMaxPlugin(plugin.LoaderImporterMaxPlugin):
    plugin_name = 'load_max'

    load_modes = load_const.LOAD_MODES

    def _get_max_options(self, load_options):
        self.logger.debug("No options implemented")
        return {}

    def run(self, context=None, data=None, options=None):


        load_mode = options.get('load_mode', self.load_modes.keys()[0])
        load_options = options.get('load_options', {})
        load_mode_fn = self.load_modes.get(load_mode, self.load_modes.keys()[0])

        max_options = {}
        if load_options:
            max_options = self._get_max_options(load_options)

        results = {}
        paths_to_import = data
        for component_path in paths_to_import:
            load_result = None
            self.logger.debug('Loading path {}'.format(component_path))

            load_result = load_mode_fn(component_path, max_options)

            results[component_path] = load_result

        return results


def register(api_object, **kw):
    plugin = LoadMaxPlugin(api_object)
    plugin.register()
