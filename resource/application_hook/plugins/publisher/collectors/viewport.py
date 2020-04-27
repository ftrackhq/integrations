# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline_3dsmax import plugin


class CollectViewportMaxPlugin(plugin.PublisherCollectorMaxPlugin):
    plugin_name = 'viewport'

    def run(self, context=None, data=None, options=None):
        viewport_index = options.get('viewport_index', -1)
        if viewport_index != -1:
            return [viewport_index]
        return []


def register(api_object, **kw):
    plugin = CollectViewportMaxPlugin(api_object)
    plugin.register()
