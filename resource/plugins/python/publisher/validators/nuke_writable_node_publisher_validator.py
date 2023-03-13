# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import ftrack_api
import os

from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_nuke import utils as nuke_utils

import nuke


class NukeWritableNodePublisherValidatorPlugin(
    plugin.NukePublisherValidatorPlugin
):
    '''Nuke writeable type publisher validator'''

    plugin_name = 'nuke_writable_node_publisher_validator'

    def run(self, context_data=None, data=None, options=None):
        '''Return true if the collected Nuke node supplied with *data* can have a write node attached to it'''
        node_name = None
        for collector in data:
            for result in collector['result']:
                if 'node_name' in result:
                    node_name = result['node_name']
                    break
            if node_name:
                break

        if node_name:
            scene_node = nuke.toNode(node_name)
            selected_nodes = nuke.selectedNodes()
            nuke_utils.clean_selection()

            write_node = nuke.createNode('Write')
            if not write_node.setInput(0, scene_node):
                msg = "The selected node can't be connected to a write node"
                self.logger.error(msg)
                return (False, {'message': msg})
            # delete temporal write node
            nuke.delete(write_node)
            # restore selection
            nuke_utils.clean_selection()
            for node in selected_nodes:
                node['selected'].setValue(True)
        else:
            self.logger.info('No collected script node to validate')
        return True


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeWritableNodePublisherValidatorPlugin(api_object)
    plugin.register()
