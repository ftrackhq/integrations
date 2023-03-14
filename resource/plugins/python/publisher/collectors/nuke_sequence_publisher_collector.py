# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import ftrack_api

import nuke

from ftrack_connect_pipeline_nuke import plugin


class NukeSequencePublisherCollectorPlugin(
    plugin.NukePublisherCollectorPlugin
):
    '''Nuke image sequence / movie collector plugin'''

    plugin_name = 'nuke_sequence_publisher_collector'

    def fetch(self, context_data=None, data=None, options=None):
        '''Fetch all selected nodes in nuke, match against class name if supplied in *options*'''
        selected_nodes = nuke.selectedNodes()
        if len(selected_nodes) == 0:
            selected_nodes = nuke.allNodes()
        node_names = []
        for node in selected_nodes:
            if (
                len(options.get('classname') or "") > 0
                and node.Class().find(options['classname']) == -1
            ):
                continue
            node_names.append(node.name())
        return node_names

    def run(self, context_data=None, data=None, options=None):
        '''Build collected objects based on *options*'''
        mode = options['mode']
        if mode in ['render_selected', 'render_create_write']:
            node_name = options.get('node_name')
            result = {
                'node_name': node_name,
            }
            if mode == 'render_create_write':
                result['create_write'] = True
        elif mode in ['render_from_sequence']:
            image_sequence_path = options.get('image_sequence_path')
            result = {'image_sequence_path': image_sequence_path}
        else:
            media_path = options.get('media_path')
            result = {'media_path': media_path}
        return [result]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeSequencePublisherCollectorPlugin(api_object)
    plugin.register()
