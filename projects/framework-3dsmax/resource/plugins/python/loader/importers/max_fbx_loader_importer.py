# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
from pymxs import runtime as rt

import ftrack_api

from ftrack_connect_pipeline_3dsmax import plugin
from ftrack_connect_pipeline_3dsmax.constants.asset import modes as load_const
from ftrack_connect_pipeline_3dsmax.constants import asset as asset_const


class MaxFbxLoaderImporterPlugin(plugin.MaxLoaderImporterPlugin):
    plugin_name = 'max_fbx_loader_importer'

    load_modes = load_const.LOAD_MODES

    def _get_max_options(self, load_options):
        max_options = {}

        if load_options.get('preserve_references'):
            max_options['pr'] = load_options.get('preserve_references')
        if load_options.get('add_namespace'):
            max_options['ns'] = load_options.get('namespace_option')

        return max_options

    def run(self, context_data=None, data=None, options=None):
        '''Import collected FBX objects provided with *data* into Max based on *options*'''
        load_options = options.get('load_options', {})

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
            self.logger.debug('Loading FBX path {}'.format(component_path))

            try:
                for key, value in list(options.items()):
                    if key.startswith('FBX'):
                        key = key[3:]
                        self.logger.debug(
                            'Setting parameter {}: {}'.format(key, value)
                        )
                        rt.FBXExporterSetParam(key, value)

                load_result = rt.importFile(
                    component_path, rt.name("noPrompt")
                )
            except RuntimeError as e:
                return False, {'message': self.logger.error(str(e))}

            results[component_path] = load_result

        return results


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MaxFbxLoaderImporterPlugin(api_object)
    plugin.register()
