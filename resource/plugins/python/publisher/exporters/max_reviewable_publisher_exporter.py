# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import tempfile
import glob
import platform

# import maya.cmds as cmds

from ftrack_connect_pipeline_3dsmax import plugin
import ftrack_api


class MaxReviewablePublisherExporterPlugin(plugin.MaxPublisherExporterPlugin):
    plugin_name = 'max_reviewable_publisher_exporter'

    def run(self, context_data=None, data=None, options=None):
        '''Export a Max reviewable to a temp file for publish'''
        collected_objects = []
        for collector in data:
            collected_objects.extend(collector['result'])
        full_path = None

        return [full_path]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MaxReviewablePublisherExporterPlugin(api_object)
    plugin.register()
