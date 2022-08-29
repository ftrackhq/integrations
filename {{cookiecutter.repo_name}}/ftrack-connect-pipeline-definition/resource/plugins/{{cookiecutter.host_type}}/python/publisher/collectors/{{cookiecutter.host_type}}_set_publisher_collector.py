# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

# import maya.cmds as cmds

import ftrack_api

from ftrack_connect_pipeline_{{cookiecutter.host_type}} import plugin


class {{cookiecutter.host_type|capitalize}}SetPublisherCollectorPlugin(plugin.{{cookiecutter.host_type|capitalize}}PublisherCollectorPlugin):
    plugin_name = '{{cookiecutter.host_type}}_set_publisher_collector'

    def run(self, context_data=None, data=None, options=None):

        set_name = options['set_name']
        # return cmds.sets(set_name, q=True)


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = {{cookiecutter.host_type|capitalize}}SetPublisherCollectorPlugin(api_object)
    plugin.register()
