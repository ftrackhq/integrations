# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import ftrack_api

import nuke
import nukescripts

from ftrack_connect_pipeline_nuke import plugin


class NukeNodesPublisherCollectorPlugin(plugin.NukePublisherCollectorPlugin):
    '''Nuke multiple nodes publisher collector plugin'''

    plugin_name = 'nuke_nodes_publisher_collector'

    def select(self, context_data=None, data=None, options=None):
        '''Select all the items in the given plugin *options*'''
        selected_items = options.get('selected_items', [])
        nukescripts.clear_selection_recursive()
        for node_name in selected_items:
            n = nuke.toNode(node_name)
            if n:
                n.setSelected(True)

    def fetch(self, context_data=None, data=None, options=None):
        '''Return a dictionary with all selected nodes, or all nodes
        if none selected'''
        selected_nodes = nuke.selectedNodes()
        if len(selected_nodes) > 0:
            return [n.name() for n in selected_nodes]
        else:
            return [n.name() for n in nuke.allNodes()]

    def run(self, context_data=None, data=None, options=None):
        '''Return the node name passed on the plugin *options*'''
        nuke_objects = options.get('collected_objects', [])
        return nuke_objects


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeNodesPublisherCollectorPlugin(api_object)
    plugin.register()
