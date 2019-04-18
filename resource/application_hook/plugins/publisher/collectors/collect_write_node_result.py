# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import nuke

from ftrack_connect_pipeline_nuke import plugin


class CollectWriteResultNodeNukePlugin(plugin.CollectorNukePlugin):
    plugin_name = 'write_node_result'

    def run(self, context=None, data=None, options=None):

        node_name = options['node_name']
        node = nuke.toNode(node_name)
        return node_name

def register(api_object, **kw):
    plugin = CollectWriteResultNodeNukePlugin(api_object)
    plugin.register()

