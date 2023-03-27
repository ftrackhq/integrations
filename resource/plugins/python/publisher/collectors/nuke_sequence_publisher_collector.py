# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os

import nuke

import ftrack_api

from ftrack_connect_pipeline_nuke import plugin


class NukeSequencePublisherCollectorPlugin(
    plugin.NukePublisherCollectorPlugin
):
    '''Nuke image sequence collector plugin'''

    plugin_name = 'nuke_sequence_publisher_collector'

    def fetch(self, context_data=None, data=None, options=None):
        '''Fetch all selected nodes in nuke, match against class name if supplied
        in *options*'''
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
            # Determine if is a compatible write node
            is_compatible_write_node = False
            if (
                node.Class() == 'Write'
                and node.knob('file')
                and node.knob('first')
                and node.knob('last')
            ):
                node_file_path = node.knob('file').value()
                if not os.path.splitext(node_file_path.lower())[-1] in [
                    '.mov',
                    '.mxf',
                    '.avi',
                    '.r3d',
                ]:
                    is_compatible_write_node = True
            node_names.append((node.name(), is_compatible_write_node))
        return node_names

    def run(self, context_data=None, data=None, options=None):
        '''Build collected objects based on *options*'''
        mode = options['mode']
        result = None
        if mode in ['render_selected', 'render_create_write']:
            node_name = options.get('node_name')
            result = {
                'node_name': node_name,
            }
            if mode == 'render_create_write':
                result['create_write'] = True
        elif mode == 'pickup':
            image_sequence_path = options.get('image_sequence_path')
            result = {'image_sequence_path': image_sequence_path}
        return [result]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeSequencePublisherCollectorPlugin(api_object)
    plugin.register()
