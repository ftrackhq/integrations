# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import nuke
import os
import sys
import glob
import re
import traceback

from ftrack_connect_pipeline_nuke import plugin


class CollectWriteResultNodeNukePlugin(plugin.CollectorNukePlugin):
    plugin_name = 'write_node_result'

    def run(self, context=None, data=None, options=None):

        node_name = options['node_name']
        node = nuke.toNode(node_name)
        if not node:
            raise Exception('Node {} not found'.format(node))

        if node.Class() != 'Write':
            raise Exception('Node {} is not of type Write'.format(node))

        filepath = node['file'].getValue()
        # todo: use self.

        return filepath


def register(api_object, **kw):
    plugin = CollectWriteResultNodeNukePlugin(api_object)
    plugin.register()

