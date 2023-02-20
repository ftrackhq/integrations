# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import hou

from ftrack_connect_pipeline_houdini.utils import (
    custom_commands as houdini_utils,
)

from ftrack_connect_pipeline_houdini import plugin
import ftrack_api


class HoudiniScenePublisherCollectorPlugin(
    plugin.HoudiniPublisherCollectorPlugin
):
    plugin_name = 'houdini_scene_publisher_collector'

    def run(self, context_data=None, data=None, options=None):
        '''Collect and return the scene name or the paths of selected objects'''
        export_option = options.get("export", 'scene')
        if export_option == 'scene':
            return [hou.hipFile.path()]
        else:
            selected_objects = hou.selectedNodes()
            objPath = hou.node('/obj')
            geometry_objects = objPath.glob('*')
            collected_objects = []
            for obj in selected_objects:
                if obj in geometry_objects:
                    collected_objects.append(obj.path())
            return collected_objects


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = HoudiniScenePublisherCollectorPlugin(api_object)
    plugin.register()
