# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import six

from ftrack_connect_pipeline_houdini import plugin
from ftrack_connect_pipeline_houdini.constants.asset import modes as load_const
from ftrack_connect_pipeline_houdini.constants import asset as asset_const
import ftrack_api


class HoudiniNativeLoaderImporterPlugin(plugin.HoudiniLoaderImporterPlugin):
    plugin_name = 'houdini_native_loader_importer'

    load_modes = load_const.LOAD_MODES

    def _get_houdini_options(self, load_options):
        houdini_options = {}

        houdini_options['load_mode'] = load_options.get('load_mode')
        houdini_options['MergeOverwriteOnConflict'] = load_options.get(
            'MergeOverwriteOnConflict'
        )

        return houdini_options

    def run(self, context_data=None, data=None, options=None):
        '''Load/merge geometry into Houdini from collected paths provided with *data* based on *options*'''

        load_mode = options.get('load_mode', list(self.load_modes.keys())[0])
        load_options = options.get('load_options', {})
        load_mode_fn = self.load_modes.get(load_mode)

        houdini_options = {}
        if load_options:
            houdini_options = self._get_houdini_options(load_options)
        houdini_options['context_data'] = context_data

        results = {}
        paths_to_import = []
        for collector in data:
            paths_to_import.append(
                collector['result'].get(asset_const.COMPONENT_PATH)
            )
        for component_path in paths_to_import:
            self.logger.debug('Loading path {}'.format(component_path))

            load_result = load_mode_fn(
                component_path,
                context_data=context_data,
                options=houdini_options,
            )

            if not six.PY2:
                results[component_path] = (
                    load_result.path()
                    if (not isinstance(load_result, str))
                    else load_result
                )
            else:
                results[component_path] = (
                    load_result.path()
                    if (
                        not isinstance(load_result, str)
                        and not isinstance(load_result, unicode)
                    )
                    else load_result
                )

        return results


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = HoudiniNativeLoaderImporterPlugin(api_object)
    plugin.register()
