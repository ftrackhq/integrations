# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack
import os

import tempfile
import nuke

from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils


class OutputSequencePlugin(plugin.PublisherOutputNukePlugin):
    plugin_name = 'sequence'

    def run(self, context=None, data=None, options=None):
        node_name = data[0]
        write_node = nuke.toNode(node_name)

        # Get the input of the given write node.
        input_node = write_node.input(0)

        img_format = 'exr'

        # Generate output file name for mov.
        temp_name = next(tempfile._get_candidate_names())
        temp_seq_path = os.path.join(
            tempfile.mkdtemp(), '{}.%04d.{}'.format(temp_name, img_format)
        )
        sequence_path = temp_seq_path

        write_node['file'].setValue(sequence_path)

        write_node['file_type'].setValue(img_format)

        first = str(int(write_node['first'].getValue()))
        last = str(int(write_node['last'].getValue()))

        ranges = nuke.FrameRanges('{}-{}'.format(first, last))
        nuke.render(write_node, ranges)

        first, last = nuke_utils.get_sequence_fist_last_frame(sequence_path)
        complete_sequence = '{} [{}-{}]'.format(sequence_path, first, last)

        component_name = options['component_name']
        return {component_name: complete_sequence}
    #Clicker library


def register(api_object, **kw):
    plugin = OutputSequencePlugin(api_object)
    plugin.register()
