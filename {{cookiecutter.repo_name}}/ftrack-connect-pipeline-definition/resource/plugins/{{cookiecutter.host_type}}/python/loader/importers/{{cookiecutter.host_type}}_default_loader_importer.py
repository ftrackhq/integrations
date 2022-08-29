# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import os

# import maya.cmds as cmds

from ftrack_connect_pipeline_{{cookiecutter.host_type}} import plugin
from ftrack_connect_pipeline_{{cookiecutter.host_type}}.constants.asset import modes as load_const
import ftrack_api


class {{cookiecutter.host_type|capitalize}}DefaultLoaderImporterPlugin(plugin.{{cookiecutter.host_type|capitalize}}LoaderImporterPlugin):
    plugin_name = '{{cookiecutter.host_type}}_default_loader_importer'

    load_modes = load_const.LOAD_MODES

    def _get_{{cookiecutter.host_type}}_options(self, load_options):
        {{cookiecutter.host_type}}_options = {}

        if load_options.get('preserve_references'):
            {{cookiecutter.host_type}}_options['pr'] = load_options.get('preserve_references')
        if load_options.get('add_namespace'):
            {{cookiecutter.host_type}}_options['ns'] = load_options.get('namespace_option')

        return {{cookiecutter.host_type}}_options

    def run(self, context_data=None, data=None, options=None):
        # cmds.loadPlugin('fbxmaya.so', qt=1)
        load_mode = options.get('load_mode', list(self.load_modes.keys())[0])
        load_options = options.get('load_options', {})
        load_mode_fn = self.load_modes.get(
            load_mode, list(self.load_modes.keys())[0]
        )

        {{cookiecutter.host_type}}_options = {}
        if load_options:
            {{cookiecutter.host_type}}_options = self._get_{{cookiecutter.host_type}}_options(load_options)

        results = {}

        paths_to_import = []
        for collector in data:
            paths_to_import.extend(collector['result'])

        for component_path in paths_to_import:
            self.logger.debug('Loading path {}'.format(component_path))
            if {{cookiecutter.host_type}}_options.get('ns') == 'file_name':
                {{cookiecutter.host_type}}_options['ns'] = os.path.basename(component_path).split(
                    "."
                )[0]
            elif {{cookiecutter.host_type}}_options.get('ns') == 'component':
                {{cookiecutter.host_type}}_options['ns'] = data[0].get('name')

            load_result = load_mode_fn(component_path, {{cookiecutter.host_type}}_options)

            results[component_path] = load_result

        return results


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = {{cookiecutter.host_type|capitalize}}DefaultLoaderImporterPlugin(api_object)
    plugin.register()
