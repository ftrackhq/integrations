# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack
import re

import maya.cmds as cmd

from ftrack_connect_pipeline_maya import plugin


class CollectFromRegexMayaPlugin(plugin.PublisherCollectorMayaPlugin):
    plugin_name = 'from_regex'

    def run(self, context=None, data=None, options=None):
        expr = options['expression']
        dag_objs = cmd.ls(ap=True, assemblies=True, dag=True)
        matched_objs = []
        for obj in dag_objs:
            matched_obj = re.findall(expr, obj)
            matched_objs += matched_obj
        if matched_objs:
            cmd.select(matched_objs, r=True)
        else:
            self.logger.error(
                'No objects matched the expression {}'.format(expr)
            )
            return []
        selection = cmd.ls(sl=True)
        return selection


def register(api_object, **kw):
    plugin = CollectFromRegexMayaPlugin(api_object)
    plugin.register()

