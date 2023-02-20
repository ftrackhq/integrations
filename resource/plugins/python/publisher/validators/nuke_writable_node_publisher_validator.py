# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import ftrack_api
import os

from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils

import nuke


class NukeWritableNodePublisherValidatorPlugin(
    plugin.NukePublisherValidatorPlugin
):
    '''Nuke writeable type publisher validator'''

    plugin_name = 'nuke_writable_node_publisher_validator'

    def run(self, context_data=None, data=None, options=None):
        '''Return true if the collected Nuke node supplied with *data* can have a write node attached to it'''
        collected_objects = []
        for collector in data:
            collected_objects.extend(collector['result'])

        if len(collected_objects) != 1:
            msg = 'No single node selected!'
            self.logger.error(msg)
            return (False, {'message': msg})
        scene_node = nuke.toNode(collected_objects[0])
        selected_nodes = nuke.selectedNodes()
        nuke_utils.cleanSelection()

        write_node = nuke.createNode('Write')
        if not write_node.setInput(0, scene_node):
            msg = "The selected node can't be connected to a write node"
            self.logger.error(msg)
            return (False, {'message': msg})
        # delete temporal write node
        nuke.delete(write_node)
        # restore selection
        nuke_utils.cleanSelection()
        for node in selected_nodes:
            node['selected'].setValue(True)
        return True


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeWritableNodePublisherValidatorPlugin(api_object)
    plugin.register()
