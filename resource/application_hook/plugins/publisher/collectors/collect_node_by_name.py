# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import nuke

from ftrack_connect_pipeline_nuke import plugin


class CollectNodeNameNukePlugin(plugin.CollectorNukePlugin):
    plugin_name = 'node_name'

    def run(self, context=None, data=None, options=None):

        node_name = options['node_name']
        return nuke.toNode(node_name)


def register(api_object, **kw):
    plugin = CollectNodeNameNukePlugin(api_object)
    plugin.register()

