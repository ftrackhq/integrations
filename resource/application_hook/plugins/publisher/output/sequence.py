# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack
import os
import clique
import tempfile

from ftrack_connect_pipeline_nuke import plugin

import nuke


class OutputSequencePlugin(plugin.PublisherOutputNukePlugin):
    plugin_name = 'sequence'

    def run(self, context=None, data=None, options=None):
        node_name = data[0]
        write_node = nuke.toNode(node_name)

        # Get the input of the given write node.
        input_node = write_node.input(0)

        default_file_format = str(options.get('file_format'))
        selected_file_format = str(options.get('image_format'))
        default_file_format_options = options.get('file_format_options')

        # Generate output file name for mov.
        temp_name = tempfile.NamedTemporaryFile()

        first = str(int(write_node['first'].getValue()))
        last = str(int(write_node['last'].getValue()))
        digit_len = int(len(last)+1)

        temp_seq_path = '{}.%0{}d.{}'.format(
            temp_name.name, digit_len, selected_file_format
        )
        sequence_path = clique.parse(
            '{} [{}-{}]'.format(temp_seq_path, first, last)
        )

        write_node['file'].setValue(temp_seq_path)

        write_node['file_type'].setValue(selected_file_format)
        if selected_file_format == default_file_format:
            for k, v in default_file_format_options.items():
                write_node[k].setValue(int(v))

        ranges = nuke.FrameRanges('{}-{}'.format(first, last))
        nuke.render(write_node, ranges)

        component_name = options['component_name']
        return {component_name: str(sequence_path)}


def register(api_object, **kw):
    plugin = OutputSequencePlugin(api_object)
    plugin.register()
