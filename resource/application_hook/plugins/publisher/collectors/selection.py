# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import maya.cmds as cmd

from ftrack_connect_pipeline_maya import plugin
from ftrack_connect_pipeline import constants


class CollectCameraMayaPlugin(plugin.PublisherCollectorMayaPlugin):
    plugin_name = 'selection'

    def run(self, context=None, data=None, options=None):
        selection = cmd.ls(sl=True)
        return selection


def register(api_object, **kw):
    plugin = CollectCameraMayaPlugin(api_object)
    plugin.register()

