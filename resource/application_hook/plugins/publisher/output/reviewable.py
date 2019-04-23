# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import sys
import tempfile
import os
import glob
import re
import traceback
import nuke

from ftrack_connect_pipeline_nuke import plugin


class ExtractSequencePlugin(plugin.ExtractorNukePlugin):
    plugin_name = 'reviewable'

    def run(self, context=None, data=None, options=None):
        node_name = data[0]
        write_node = nuke.toNode(node_name)

        # Get the input of the given write node.
        input_node = write_node.input(0)

        # Generate output file name for mov.
        temp_review_mov = tempfile.NamedTemporaryFile(delete=False, suffix='.mov').name

        first = str(int(nuke.root().knob('first_frame').value()))
        last = str(int(nuke.root().knob('last_frame').value()))

        # Create a new write_node.
        review_node = nuke.createNode('Write')
        review_node.setInput(0, input_node)
        review_node['file'].setValue(temp_review_mov)
        review_node['file_type'].setValue('mov')
        review_node['mov64_codec'].setValue('png')

        if write_node['use_limit'].getValue():
            first = write_node['first'].getValue()
            last = write_node['last'].getValue()
            review_node['use_limit'].setValue(True)

        ranges = nuke.FrameRanges('{0}-{1}'.format(first, last))
        nuke.render(review_node, ranges)

        # delete thumbnail network after render
        nuke.delete(review_node)

        component_name = options['component_name']
        return {component_name: temp_review_mov}


def register(api_object, **kw):
    plugin = ExtractSequencePlugin(api_object)
    plugin.register()
