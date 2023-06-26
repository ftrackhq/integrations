# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

import ftrack_api

from ftrack_connect_pipeline_{{cookiecutter.host_type}} import plugin
from ftrack_connect_pipeline_{{cookiecutter.host_type}} import utils as {{cookiecutter.host_type}}_utils


class {{cookiecutter.host_type_capitalized}}NativeOpenerFinalizerPlugin(plugin.{{cookiecutter.host_type_capitalized}}OpenerFinalizerPlugin):
    plugin_name = '{{cookiecutter.host_type}}_native_opener_finalizer'

    def run(self, context_data=None, data=None, options=None):
        '''Save opened {{cookiecutter.host_type_capitalized}} scene in temp to avoid being overwritten'''

        result = {}

        self.logger.debug('Rename {{cookiecutter.host_type_capitalized}} scene on open')
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
    plugin = {{cookiecutter.host_type_capitalized}}NativeOpenerFinalizerPlugin(api_object)
    plugin.register()
