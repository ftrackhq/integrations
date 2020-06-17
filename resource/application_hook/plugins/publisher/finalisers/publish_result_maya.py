# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
from ftrack_connect_pipeline_maya import plugin
import ftrack_api

class FtrackPublishMayaPlugin(plugin.PublisherFinaliserMayaPlugin):
    plugin_name = 'result_maya'

    def run(self, context=None, data=None, options=None):
        return {}


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = FtrackPublishMayaPlugin(api_object)
    plugin.register()
