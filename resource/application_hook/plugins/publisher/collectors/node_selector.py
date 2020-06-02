# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import nuke

from ftrack_connect_pipeline_nuke import plugin


class NodeSelectorNukePlugin(plugin.PublisherCollectorNukePlugin):
    plugin_name = 'node_selector'

    def run(self, context=None, data=None, options=None):

        node_name = options['node_name']
        return [node_name]


def register(api_object, **kw):
    plugin = NodeSelectorNukePlugin(api_object)
    plugin.register()

