# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import ftrack_api

import nuke

from ftrack_connect_pipeline_nuke import plugin


class NukeDefaultPublisherCollectorPlugin(plugin.NukePublisherCollectorPlugin):
    plugin_name = 'nuke_default_publisher_collector'

    def fetch(self, context_data=None, data=None, options=None):
        '''Fetch all selecated nodes in nuke'''
        selected_nodes = nuke.selectedNodes()
        node_names = [node.name() for node in selected_nodes]
        return node_names

    def run(self, context_data=None, data=None, options=None):
        '''Return the node name passed on the plugin *options*'''
        node_name = options.get('node_name', [])
        return [node_name]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeDefaultPublisherCollectorPlugin(api_object)
    plugin.register()
