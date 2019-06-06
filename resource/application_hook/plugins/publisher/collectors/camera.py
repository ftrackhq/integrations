# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import MaxPlus
from ftrack_connect_pipeline_3dsmax import plugin


class CollectCameraMaxPlugin(plugin.CollectorMaxPlugin):
    plugin_name = 'camera'
    MAX_CAMERA_CLASS_ID = 32

    def create_camera_instances(self, node, selection, cameras):
        if node.Object.SuperClassID == self.MAX_CAMERA_CLASS_ID:
            name = node.GetName()
            if name in selection:
                cameras.append(name)

    def run(self, context=None, data=None, options=None):
        camera_name = options.get('camera_name', 'persp')
        # TODO filter cameras with the one we should be looking for...

        cameras = []
        # Build a set with the selection to check quickly if a node is selected.
        selection = set()
        for n in MaxPlus.SelectionManager.GetNodes():
            selection.add(n.GetName())

        root = MaxPlus.Core.GetRootNode()
        for node in root.Children:
            self.create_camera_instances(node, selection, cameras)

        return cameras


def register(api_object, **kw):
    plugin = CollectCameraMaxPlugin(api_object)
    plugin.register()
