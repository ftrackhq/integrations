# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline_nuke import plugin

import nuke


class NoneEmptyValidatorPlugin(plugin.PublisherValidatorNukePlugin):
    plugin_name = 'node_type'

    def run(self, context=None, data=None, options=None):
        node_type = options['node_type']
        node_name = data[0]
        node = nuke.toNode(node_name)
        if node.Class() != node_type:
            self.logger.error('Node {} is not of type {}'.format(node, node_type))
            return False

        return bool(node_name)


def register(api_object, **kw):
    plugin = NoneEmptyValidatorPlugin(api_object)
    plugin.register()
