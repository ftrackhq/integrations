# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

import ftrack_api

import re

# import maya.cmds as cmds

from ftrack_connect_pipeline_{{cookiecutter.host_type}} import plugin


class {{cookiecutter.host_type_capitalized}}RegexPublisherCollectorPlugin(plugin.{{cookiecutter.host_type_capitalized}}PublisherCollectorPlugin):
    plugin_name = '{{cookiecutter.host_type}}_regex_publisher_collector'

    def run(self, context_data=None, data=None, options=None):
        '''Select and collect nodes matching regular expression from *options*'''
        expr = options['expression']
        # dag_objs = cmds.ls(ap=True, assemblies=True, dag=True)
        matched_objs = []
        for obj in dag_objs:
            matched_obj = re.findall(expr, obj)
            matched_objs += matched_obj
        if matched_objs:
            # cmds.select(matched_objs, r=True)
        else:
            self.logger.error(
                'No objects matched the expression {}'.format(expr)
            )
            return []
        # selection = cmds.ls(sl=True)
        return selection


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = {{cookiecutter.host_type_capitalized}}RegexPublisherCollectorPlugin(api_object)
    plugin.register()
