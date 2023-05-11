# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import os

import maya.cmds as cmds

from ftrack_connect_pipeline_maya import plugin
from ftrack_connect_pipeline_maya.constants.asset import modes as load_const
from ftrack_connect_pipeline_maya.constants import asset as asset_const
import ftrack_api


class MayaNativeLoaderImporterPlugin(plugin.MayaLoaderImporterPlugin):
    '''Plugin for loading native Maya binary or ASCII files'''

    plugin_name = 'maya_native_loader_importer'

    load_modes = load_const.LOAD_MODES

    def _get_maya_options(self, load_options):
        maya_options = {}

        if load_options.get('preserve_references'):
            maya_options['pr'] = load_options.get('preserve_references')
        if load_options.get('add_namespace'):
            maya_options['ns'] = load_options.get('namespace_option')

        return maya_options

    def run(self, context_data=None, data=None, options=None):
        '''Load an asset in Maya based on *options* and pointed out by collected path in *data*'''
        load_mode = options.get('load_mode', list(self.load_modes.keys())[0])
        load_options = options.get('load_options', {})
        load_mode_fn = self.load_modes.get(
            load_mode, list(self.load_modes.keys())[0]
        )

        maya_options = {}
        if load_options:
            maya_options = self._get_maya_options(load_options)

        results = {}

        paths_to_import = []
        for collector in data:
            paths_to_import.append(
                collector['result'].get(asset_const.COMPONENT_PATH)
            )

        for component_path in paths_to_import:
            self.logger.debug('Loading path {}'.format(component_path))

            if maya_options.get('ns') == 'file_name':
                maya_options['ns'] = os.path.basename(component_path).split(
                    "."
                )[0]
            elif maya_options.get('ns') == 'component':
                maya_options['ns'] = data[0].get('name')

            if component_path.lower().endswith('.fbx'):
                cmds.loadPlugin('fbxmaya.so', qt=1)

            load_result = load_mode_fn(component_path, maya_options)

            results[component_path] = load_result

        return results


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MayaNativeLoaderImporterPlugin(api_object)
    plugin.register()
