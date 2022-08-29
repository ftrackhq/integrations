# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

import ftrack_api

from ftrack_connect_pipeline_{{cookiecutter.host_type}} import plugin
from ftrack_connect_pipeline_{{cookiecutter.host_type}}.utils import custom_commands as {{cookiecutter.host_type}}_utils


class {{cookiecutter.host_type|capitalize}}DefaultOpenerFinalizerPlugin(plugin.{{cookiecutter.host_type|capitalize}}OpenerFinalizerPlugin):
    plugin_name = '{{cookiecutter.host_type}}_default_opener_finalizer'

    def run(self, context_data=None, data=None, options=None):
        result = {}

        self.logger.debug('Rename {{cookiecutter.host_type|capitalize}} scene on open')
        save_path, message = {{cookiecutter.host_type}}_utils.save(
            context_data['context_id'], self.session, save=False
        )
        if save_path:
            result['save_path'] = save_path
        else:
            result = False

        return (result, {'message': message})


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = {{cookiecutter.host_type|capitalize}}DefaultOpenerFinalizerPlugin(api_object)
    plugin.register()
