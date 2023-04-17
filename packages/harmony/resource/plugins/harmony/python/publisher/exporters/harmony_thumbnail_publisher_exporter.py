# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

# import maya.cmds as cmds

import ftrack_api
from ftrack_connect_pipeline_harmony import plugin


class HarmonyThumbnailPublisherExporterPlugin(
    plugin.HarmonyPublisherExporterPlugin
):
    plugin_name = 'harmony_thumbnail_publisher_exporter'

    def run(self, context_data=None, data=None, options=None):
        '''Export a Harmony thumbnail to a temp file for publish'''

        collected_objects = []
        for collector in data:
            collected_objects.extend(collector['result'])

        path = None

        return [path]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = HarmonyThumbnailPublisherExporterPlugin(api_object)
    plugin.register()
