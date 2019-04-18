# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline_nuke import plugin

import nuke


class NoneEmptyValidatorPlugin(plugin.ValidatorNukePlugin):
    plugin_name = 'node_type'

    def run(self, context=None, data=None, options=None):
        node_type = options['node_type']
        node_name = data[0]
        self.logger.info('validating {} as node type {}'.format(node_name, node_type))
        node = nuke.toNode(node_name)
        if node.Class() != node_type:
            self.logger.error('Node {} is not of type Write'.format(node))
            return False

        return bool(node_name)


def register(api_object, **kw):
    plugin = NoneEmptyValidatorPlugin(api_object)
    plugin.register()
