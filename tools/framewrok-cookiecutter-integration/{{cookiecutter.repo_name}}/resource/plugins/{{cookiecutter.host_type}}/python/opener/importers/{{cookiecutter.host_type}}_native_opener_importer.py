# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

import os

# import maya.cmds as cmds

from ftrack_connect_pipeline_{{cookiecutter.host_type}} import plugin
from ftrack_connect_pipeline_{{cookiecutter.host_type}}.constants.asset import modes as load_const
import ftrack_api


class {{cookiecutter.host_type_capitalized}}NativeOpenerImporterPlugin(plugin.{{cookiecutter.host_type_capitalized}}OpenerImporterPlugin):
    plugin_name = '{{cookiecutter.host_type}}_native_opener_importer'

    def run(self, context_data=None, data=None, options=None):
        '''Open a {{cookiecutter.host_type_capitalized}} scene from path stored in collected object provided with *data*'''

        load_mode = load_const.OPEN_MODE
        load_mode_fn = self.load_modes.get(
            load_mode, list(self.load_modes.keys())[0]
        )

        {{cookiecutter.host_type}}_options = {}

        results = {}

        paths_to_import = []
        for collector in data:
            paths_to_import.extend(collector['result'])

        for component_path in paths_to_import:
            self.logger.debug('Opening path {}'.format(component_path))

            load_result = load_mode_fn(component_path, {{cookiecutter.host_type}}_options)

            results[component_path] = load_result

        return results


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = {{cookiecutter.host_type_capitalized}}NativeOpenerImporterPlugin(api_object)
    plugin.register()
