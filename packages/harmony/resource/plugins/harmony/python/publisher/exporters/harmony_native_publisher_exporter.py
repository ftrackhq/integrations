# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import tempfile
import os

# import maya.cmds as cmds

from ftrack_connect_pipeline_harmony import utils as harmony_utils
from ftrack_connect_pipeline_harmony import plugin
import ftrack_api


class HarmonyNativePublisherExporterPlugin(plugin.HarmonyPublisherExporterPlugin):
    plugin_name = 'harmony_native_publisher_exporter'

    def run(self, context_data=None, data=None, options=None):
        '''Pick uo and export the Harmony xstage file'''
        new_file_path = None

        return [new_file_path]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    output_plugin = HarmonyNativePublisherExporterPlugin(api_object)
    output_plugin.register()
