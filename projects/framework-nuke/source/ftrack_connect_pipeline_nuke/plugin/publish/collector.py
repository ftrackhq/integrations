# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import os

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_nuke.plugin import (
    NukeBasePlugin,
    NukeBasePluginWidget,
)


class NukePublisherCollectorPlugin(
    plugin.PublisherCollectorPlugin, NukeBasePlugin
):
    supported_file_formats = []
    '''Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''

    def filter_by_class_name(self, selected_nodes, class_name):
        '''
        Filter given *selected_nodes* by given *class_name*
        '''
        # filter selected_nodes to match classname given by options
        selected_nodes = list(
            filter(lambda x: x.Class().find(class_name) != -1, selected_nodes)
        )
        return selected_nodes

    def classify_supported_write_nodes(self, selected_nodes):
        '''
        Return a dictionary with supported write_nodes and all given
        *selected_nodes*
        '''
        node_names = {'write_nodes': [], 'all_nodes': []}
        for node in selected_nodes:
            # Determine if is a compatible write node
            if (
                node.Class() == 'Write'
                and node.knob('file')
                and node.knob('first')
                and node.knob('last')
            ):
                node_file_path = node.knob('file').value()
                if (
                    os.path.splitext(node_file_path.lower())[-1]
                    in self.supported_file_formats
                ):
                    node_names['write_nodes'].append(node.name())
            node_names['all_nodes'].append(node.name())
        return node_names


class NukePublisherCollectorPluginWidget(
    pluginWidget.PublisherCollectorPluginWidget, NukeBasePluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
