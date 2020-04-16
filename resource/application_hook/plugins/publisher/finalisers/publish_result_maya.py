# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
from ftrack_connect_pipeline_maya import plugin

class FtrackPublishMayaPlugin(plugin.PublisherFinaliserMayaPlugin):
    plugin_name = 'result_maya'

    def run(self, context=None, data=None, options=None):
        return {}


def register(api_object, **kw):
    plugin = FtrackPublishMayaPlugin(api_object)
    plugin.register()
