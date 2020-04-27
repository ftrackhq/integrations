# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import pymxs

from ftrack_connect_pipeline_3dsmax import plugin


class CollectSelectionMaxPlugin(plugin.PublisherCollectorMaxPlugin):
    plugin_name = 'selection'

    def run(self, context=None, data=None, options=None):
        selection = [node.getmxsprop('name') for node in pymxs.runtime.selection]
        return selection


def register(api_object, **kw):
    plugin = CollectSelectionMaxPlugin(api_object)
    plugin.register()
