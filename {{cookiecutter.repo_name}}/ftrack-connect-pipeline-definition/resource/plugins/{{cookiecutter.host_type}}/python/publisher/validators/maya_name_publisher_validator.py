# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from ftrack_connect_pipeline_{{cookiecutter.host_type}} import plugin

# import maya.cmds as cmds

import ftrack_api


class {{cookiecutter.host_type|capitalize}}NamePublisherValidatorPlugin(plugin.{{cookiecutter.host_type|capitalize}}PublisherValidatorPlugin):
    plugin_name = '{{cookiecutter.host_type}}_name_publisher_validator'

    def run(self, context_data=None, data=None, options=None):

        collected_objects = []
        for collector in data:
            collected_objects.extend(collector['result'])

        # allObj = cmds.ls(collected_objects, tr=True)
        if not allObj:
            return False
        for obj in allObj:
            if obj.startswith('ftrack_') == False:
                return False
        return True


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = {{cookiecutter.host_type|capitalize}}NamePublisherValidatorPlugin(api_object)
    plugin.register()
