# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline_3dsmax import plugin

class PublishFinaliserMaxPlugin(plugin.PublisherFinaliserMaxPlugin):
    plugin_name = 'result.max'

    def run(self, context=None, data=None, options=None):
        return {}

def register(api_object, **kw):
    plugin = PublishFinaliserMaxPlugin(api_object)
    plugin.register()
