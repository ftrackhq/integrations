# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import ftrack_api

import nuke

from ftrack_connect_pipeline_nuke import plugin


class NukeCameraPublisherCollectorPlugin(plugin.NukePublisherCollectorPlugin):
    '''Nuke camera collector plugin'''

    plugin_name = 'nuke_camera_publisher_collector'

    def fetch(self, context_data=None, data=None, options=None):
        '''Fetch all selected camera nodes in nuke'''
        selected_nodes = nuke.selectedNodes()
        if len(selected_nodes) == 0:
            selected_nodes = nuke.allNodes()
        node_names = []
        for node in selected_nodes:
            if node.Class() in ['Camera2', 'Camera3']:
                node_names.append(node.name())
        return node_names

    def run(self, context_data=None, data=None, options=None):
        '''Return the node name passed on the plugin *options*'''
        node_name = options.get('node_name')
        return [node_name]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeCameraPublisherCollectorPlugin(api_object)
    plugin.register()
