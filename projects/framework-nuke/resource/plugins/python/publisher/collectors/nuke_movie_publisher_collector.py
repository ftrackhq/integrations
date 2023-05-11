# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os

import nuke

import ftrack_api

from ftrack_connect_pipeline_nuke import plugin


class NukeMoviePublisherCollectorPlugin(plugin.NukePublisherCollectorPlugin):
    '''Nuke movie collector plugin'''

    plugin_name = 'nuke_movie_publisher_collector'

    supported_file_formats = [".mov", ".mxf", ".avi", ".r3d"]

    def fetch(self, context_data=None, data=None, options=None):
        '''Fetch all selected nodes in nuke, match against class name if supplied in *options*'''
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
        elif mode in ['render_from_sequence']:
            image_sequence_path = options.get('image_sequence_path')
            result = {'image_sequence_path': image_sequence_path}
        elif mode == 'pickup':
            movie_path = options.get('movie_path')
            result = {'movie_path': movie_path}
        return [result]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeMoviePublisherCollectorPlugin(api_object)
    plugin.register()
