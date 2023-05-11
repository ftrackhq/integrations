# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

import hou

from ftrack_connect_pipeline_houdini import plugin
import ftrack_api


class HoudiuniCameraPublisherCollectorPlugin(
    plugin.HoudiniPublisherCollectorPlugin
):
    plugin_name = 'houdini_camera_publisher_collector'

    def fetch(self, context_data=None, data=None, options=None):
        '''Fetch all cameras from the scene'''
        collected_objects = []
        for obj in hou.node('/').allSubChildren():
            if 'cam' in obj.type().name():
                collected_objects.append(obj.path())
        return collected_objects

    def run(self, context_data=None, data=None, options=None):
        '''Return the long name of the camera from the plugin *options*'''
        collected_objects = []
        for obj in hou.selectedNodes():
            if 'cam' in obj.type().name():
                collected_objects.append(obj.path())
        return collected_objects


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = HoudiuniCameraPublisherCollectorPlugin(api_object)
    plugin.register()
