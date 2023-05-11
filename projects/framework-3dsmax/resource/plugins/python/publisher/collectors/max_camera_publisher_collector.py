# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from pymxs import runtime as rt

from ftrack_connect_pipeline_3dsmax import plugin
import ftrack_api


class MaxCameraPublisherCollectorPlugin(plugin.MaxPublisherCollectorPlugin):
    plugin_name = 'max_camera_publisher_collector'

    def fetch(self, context_data=None, data=None, options=None):
        '''Fetch all cameras from the scene'''
        cameras = []
        for obj in rt.rootScene.world.children:
            if rt.SuperClassOf(obj) == rt.camera:
                cameras.append(obj.name)
        return cameras

    def run(self, context_data=None, data=None, options=None):
        '''Return the long name of the camera from the plugin *options*'''
        camera_name = options.get('camera_name', 'persp')
        camera = rt.getNodeByName(camera_name)
        if camera:
            return [camera.name]
        return []


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MaxCameraPublisherCollectorPlugin(api_object)
    plugin.register()
