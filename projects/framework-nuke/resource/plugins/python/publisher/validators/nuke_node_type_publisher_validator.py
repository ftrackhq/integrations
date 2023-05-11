# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import ftrack_api

from ftrack_connect_pipeline_nuke import plugin

import nuke


class NukeNodeTypePublisherValidatorPlugin(
    plugin.NukePublisherValidatorPlugin
):
    '''Nuke node type publisher validator'''

    plugin_name = 'nuke_node_type_publisher_validator'

    def run(self, context_data=None, data=None, options=None):
        '''Return true if the collected Nuke node supplied with *data* matches the node type provided with *options*'''

        node_type = options['node_type']
        collected_objects = []
        for collector in data:
            collected_objects.extend(collector['result'])

        if len(collected_objects) != 1:
            msg = 'No single node selected!'
            self.logger.error(msg)
            return (False, {'message': msg})

        node_name = collected_objects[0]
        node = nuke.toNode(node_name)
        if node.Class() != node_type:
            msg = 'Node {} is not of type {}'.format(node, node_type)
            self.logger.error(msg)
            return (False, {'message': msg})
        return bool(node_name)


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeNodeTypePublisherValidatorPlugin(api_object)
    plugin.register()
