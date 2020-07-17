# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import ftrack_api

import pymxs

from ftrack_connect_pipeline_3dsmax import plugin


class CollectCameraMaxPlugin(plugin.PublisherCollectorMaxPlugin):
    plugin_name = 'camera'

    def run(self, context=None, data=None, options=None):
        camera_name = options.get('camera_name', 'persp')
        with pymxs.mxstoken():
            camera = pymxs.runtime.getNodeByName(camera_name)
        if camera:
            return [camera.name]
        return []


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = CollectCameraMaxPlugin(api_object)
    plugin.register()
