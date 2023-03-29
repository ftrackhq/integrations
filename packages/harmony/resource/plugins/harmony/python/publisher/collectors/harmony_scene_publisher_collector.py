# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

# import maya.cmds as cmds

import ftrack_api

from ftrack_connect_pipeline_harmony import utils as harmony_utils

from ftrack_connect_pipeline_harmony import plugin


class HarmonyScenePublisherCollectorPlugin(plugin.HarmonyPublisherCollectorPlugin):
    plugin_name = 'harmony_scene_publisher_collector'

    def run(self, context_data=None, data=None, options=None):
        '''Collect Harmony scene name, save to temp if unsaved'''
        export_option = options.get("export")
        if export_option and isinstance(export_option, list):
            export_option = export_option[0]
        export_object = [None]
        return export_object


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = HarmonyScenePublisherCollectorPlugin(api_object)
    plugin.register()
