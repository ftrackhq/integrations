# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import os

# import maya.cmds as cmds

from ftrack_connect_pipeline_3dsmax import plugin
from ftrack_connect_pipeline_3dsmax.constants.asset import modes as load_const
from ftrack_connect_pipeline_3dsmax.constants import asset as asset_const
import ftrack_api


class MaxNativeLoaderImporterPlugin(plugin.MaxLoaderImporterPlugin):
    plugin_name = 'max_native_loader_importer'

    load_modes = dict(
        (k, v)
        for (k, v) in list(load_const.LOAD_MODES.items())
        if k.lower() != 'open'
    )

    def _get_max_options(self, load_options):
        max_options = {}

        if load_options.get('preserve_references'):
            max_options['pr'] = load_options.get('preserve_references')
        if load_options.get('add_namespace'):
            max_options['ns'] = load_options.get('namespace_option')

        return max_options

    def run(self, context_data=None, data=None, options=None):
        '''Import collected objects provided with *data* into Max based on *options*'''
        load_mode = options.get('load_mode', list(self.load_modes.keys())[0])
        load_options = options.get('load_options', {})
        load_mode_fn = self.load_modes.get(
            load_mode, list(self.load_modes.keys())[0]
        )

        max_options = {}
        if load_options:
            max_options = self._get_max_options(load_options)

        results = {}

        paths_to_import = []
        for collector in data:
            paths_to_import.append(
                collector['result'].get(asset_const.COMPONENT_PATH)
            )

        for component_path in paths_to_import:
            self.logger.debug('Loading path {}'.format(component_path))
            if max_options.get('ns') == 'file_name':
                max_options['ns'] = os.path.basename(component_path).split(
                    "."
                )[0]
            elif max_options.get('ns') == 'component':
                max_options['ns'] = data[0].get('name')

            load_result = load_mode_fn(component_path, max_options)

            results[component_path] = (
                load_result
                if isinstance(load_result, bool)
                else bool(load_result is not None)
            )

        return results


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MaxNativeLoaderImporterPlugin(api_object)
    plugin.register()
