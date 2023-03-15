# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import ftrack_api
import os
import clique
import tempfile

from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_nuke import utils as nuke_utils

import nuke
import shutil


class NukeSequencePublisherExporterPlugin(plugin.NukePublisherExporterPlugin):
    '''Nuke image sequence exporter plugin'''

    plugin_name = 'nuke_sequence_publisher_exporter'

    def run(self, context_data=None, data=None, options=None):
        '''Export an image sequence from Nuke from collected node or supplied media with *data* based on *options*'''

        node_name = None
        image_sequence_path = None
        create_write = False
        for collector in data:
            result = collector['result'][0]
            if 'node_name' in result:
                node_name = result['node_name']
                create_write = result.get('create_write', False)
            else:
                image_sequence_path = result['image_sequence_path']

        if node_name:
            input_node = nuke.toNode(node_name)
            selected_nodes = nuke.selectedNodes()
            nuke_utils.clean_selection()
            try:
                if create_write:
                    # Create a write node and connect it to the selected input node
                    write_node = nuke.createNode('Write')
                    write_node.setInput(0, input_node)
                    write_node['first'].setValue(
                        int(
                            float(
                                options.get('start_frame')
                                or nuke.root()['first_frame'].value()
                            )
                        )
                    )
                    write_node['last'].setValue(
                        int(
                            float(
                                options.get('end_frame')
                                or nuke.root()['last_frame'].value()
                            )
                        )
                    )

                    selected_file_format = str(options.get('image_format'))
                    file_format_options = (
                        options.get('file_format_options') or {}
                    )

                    # Generate exporters file name for mov.
                    temp_name = tempfile.NamedTemporaryFile()

                    first = int(write_node['first'].getValue())
                    last = int(write_node['last'].getValue())
                    digit_len = int(len(str(last)) + 1)

                    temp_sequence_path = '{}.%0{}d.{}'.format(
                        temp_name.name, digit_len, selected_file_format
                    )
                    image_sequence_path = clique.parse(
                        '{} [{}-{}]'.format(temp_sequence_path, first, last)
                    )

                    write_node['file'].setValue(
                        temp_sequence_path.replace('\\', '/')
                    )

                    write_node['file_type'].setValue(selected_file_format)
                    if (
                        len(
                            file_format_options.get(selected_file_format) or {}
                        )
                        > 0
                    ):
                        for k, v in file_format_options[
                            selected_file_format
                        ].items():
                            write_node[k].setValue(v)

                    self.logger.debug(
                        'Rendering sequence [{}-{}] to "{}"'.format(
                            first, last, temp_sequence_path
                        )
                    )
                    nuke.render(write_node, first, last)

                    # delete temporal write node
                    nuke.delete(write_node)

                else:
                    # Assume selected node is a write node, use it to render
                    write_node = nuke.toNode(node_name)

                    if write_node is None:
                        return (
                            False,
                            {
                                'message': 'Could not load image sequence write node {}!'.format(
                                    write_node
                                )
                            },
                        )

                    file_path = write_node['file'].value()
                    if file_path is None or os.path.splitext(
                        file_path.lower()
                    )[-1] in ['.mov', '.mxf', '.avi', '.r3d']:
                        return (
                            False,
                            {
                                'message': 'No image sequence write node selected!'
                            },
                        )

                    first = int(
                        float(
                            options.get('start_frame')
                            or (
                                nuke.root()['first_frame'].value()
                                if write_node['use_limit'].getValue() == 0
                                else write_node['first'].getValue()
                            )
                        )
                    )
                    last = int(
                        float(
                            options.get('end_frame')
                            or (
                                nuke.root()['last_frame'].value()
                                if write_node['use_limit'].getValue() == 0
                                else write_node['last'].getValue()
                            )
                        )
                    )

                    self.logger.debug(
                        'Rendering sequence [{}-{}] from existing write node "{}", path: "{}"'.format(
                            first,
                            last,
                            write_node.name(),
                            write_node['file'].value(),
                        )
                    )
                    nuke.render(write_node, first, last)

                    image_sequence_path = clique.parse(
                        '{} [{}-{}]'.format(
                            write_node['file'].value(), first, last
                        )
                    )
            finally:
                # restore selection
                nuke_utils.clean_selection()
                for node in selected_nodes:
                    node['selected'].setValue(True)
        else:
            self.logger.debug(
                'Picking up rendered file sequence path for publish: "{}"'.format(
                    image_sequence_path
                )
            )

        return [str(image_sequence_path)]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeSequencePublisherExporterPlugin(api_object)
    plugin.register()
