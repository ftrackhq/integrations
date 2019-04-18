# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import nuke
import os
import sys
import glob
import re
import traceback
import clique

from ftrack_connect_pipeline_nuke import plugin


class CollectWriteResultNodeNukePlugin(plugin.CollectorNukePlugin):
    plugin_name = 'write_node_result'

    def run(self, context=None, data=None, options=None):

        node_name = options['node_name']
        node = nuke.toNode(node_name)
        if not node:
            raise Exception('Node {} not found'.format(node_name))

        if node.Class() != 'Write':
            raise Exception('Node {} is not of type Write'.format(node))

        file_path = node['file'].getValue()

        # Get start and last frame , and use them to build a parsable string
        # for clique so we can retrieve the actual frames.
        first, last = self.get_sequence_fist_last_frame(file_path)
        complete_sequence = '{} [{}-{}]'.format(file_path, first, last)
        return complete_sequence


def register(api_object, **kw):
    plugin = CollectWriteResultNodeNukePlugin(api_object)
    plugin.register()

