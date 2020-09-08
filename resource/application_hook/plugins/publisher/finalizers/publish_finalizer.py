# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import ftrack_api

from ftrack_connect_pipeline_3dsmax import plugin

class PublishFinalizerMaxPlugin(plugin.PublisherFinalizerMaxPlugin):
    plugin_name = 'result.max'

    def run(self, context=None, data=None, options=None):
        return {}

def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = PublishFinalizerMaxPlugin(api_object)
    plugin.register()
