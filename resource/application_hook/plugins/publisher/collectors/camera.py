# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import maya.cmds as cmd

from ftrack_connect_pipeline_maya import plugin


class CollectCameraMayaPlugin(plugin.PublisherCollectorMayaPlugin):
    plugin_name = 'camera'

    def run(self, context=None, data=None, options=None):
        camera_name = options.get('camera_name', 'persp')
        cameras = cmd.ls(camera_name, l=True)
        return cameras


def register(api_object, **kw):
    plugin = CollectCameraMayaPlugin(api_object)
    plugin.register()

