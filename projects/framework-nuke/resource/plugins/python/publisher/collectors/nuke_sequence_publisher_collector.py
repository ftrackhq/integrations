# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os

import nuke

import ftrack_api

from framework_nuke import plugin


class NukeSequencePublisherCollectorPlugin(
    plugin.NukePublisherCollectorPlugin
):
    '''Nuke image sequence collector plugin'''

    plugin_name = 'nuke_sequence_publisher_collector'

    supported_file_formats = [
        ".cin",
        ".dng",
        ".dpx",
        ".dtex",
        ".gif",
        ".bmp",
        ".float",
        ".pcx",
        ".png",
        ".psd",
        ".tga",
        ".jpeg",
        ".jpg",
        ".exr",
        ".dds",
        ".hdr",
        ".hdri",
        ".cgi",
        ".tif",
        ".tiff",
        ".tga",
        ".targa",
        ".yuv",
    ]

    def fetch(self, context_data=None, data=None, options=None):
        '''Fetch all selected nodes in nuke, match against class name if supplied
        in *options*'''
        selected_nodes = nuke.selectedNodes()
        if len(selected_nodes) == 0:
            selected_nodes = nuke.allNodes()

        self.supported_file_formats = (
            options.get("supported_file_formats")
            or self.supported_file_formats
        )

        # filter selected_nodes to match classname given by options
        if options.get('classname'):
            selected_nodes = self.filter_by_class_name(
                selected_nodes, options.get('classname')
            )

        node_names = self.classify_supported_write_nodes(selected_nodes)

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
