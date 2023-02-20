# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import ftrack_api
import os
import clique
import tempfile

from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils

import nuke
import shutil


class NukeSequencePublisherExporterPlugin(plugin.NukePublisherExporterPlugin):
    '''Nuke image sequence exporter plugin'''

    plugin_name = 'nuke_sequence_publisher_exporter'

    def run(self, context_data=None, data=None, options=None):
        '''Export an image sequence from Nuke from collected node with *data* based on *options*'''

        collected_objects = []
        for collector in data:
            collected_objects.extend(collector['result'])

        node_name = collected_objects[0]
        input_node = nuke.toNode(node_name)
        selected_nodes = nuke.selectedNodes()
        nuke_utils.cleanSelection()
        try:
            mode = (options.get('mode') or 'render').lower()
            if mode == 'render':
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
                file_format_options = options.get('file_format_options') or {}

                # Generate exporters file name for mov.
                temp_name = tempfile.NamedTemporaryFile()

                first = str(int(write_node['first'].getValue()))
                last = str(int(write_node['last'].getValue()))
                digit_len = int(len(last) + 1)

                temp_sequence_path = '{}.%0{}d.{}'.format(
                    temp_name.name, digit_len, selected_file_format
                )
                sequence_path = clique.parse(
                    '{} [{}-{}]'.format(temp_sequence_path, first, last)
                )

                write_node['file'].setValue(
                    temp_sequence_path.replace('\\', '/')
                )

                write_node['file_type'].setValue(selected_file_format)
                if (
                    len(file_format_options.get(selected_file_format) or {})
                    > 0
                ):
                    for k, v in file_format_options[
                        selected_file_format
                    ].items():
                        write_node[k].setValue(v)

                ranges = nuke.FrameRanges('{}-{}'.format(first, last))
                self.logger.debug(
                    'Rendering sequence [{}-{}] to "{}"'.format(
                        first, last, temp_sequence_path
                    )
                )
                nuke.render(write_node, ranges)

                # delete temporal write node
                nuke.delete(write_node)

            elif mode == 'render_write':

                # Find sequence write node among selected nodes
                write_node = None
                for node in selected_nodes:
                    if node.Class() in ['Write']:
                        # Is it a sequence?
                        if len(
                            node['file'].value() or ''
                        ) and not os.path.splitext(node['file'].value())[
                            1
                        ].lower() in [
                            '.mov',
                            '.mxf',
                        ]:
                            write_node = node
                            break
                if write_node is None:
                    return (
                        False,
                        {'message': 'No sequence write node selected!'},
                    )
                self.logger.debug(
                    'Using existing node {} file sequence path: "{}", copying to temp.'.format(
                        write_node.name(), write_node['file'].value()
                    )
                )
                first = str(int(write_node['first'].getValue()))
                last = str(int(write_node['last'].getValue()))
                ranges = nuke.FrameRanges('{}-{}'.format(first, last))
                self.logger.debug(
                    'Rendering sequence [{}-{}] to "{}"'.format(
                        first, last, write_node['file'].value()
                    )
                )
                nuke.render(write_node, ranges)

                sequence_path = clique.parse(
                    '{} [{}-{}]'.format(
                        write_node['file'].value(), first, last
                    )
                )
            else:
                # Find sequence write/read node among selected nodes
                file_node = None
                for node in selected_nodes:
                    if node.Class() in ['Read', 'Write']:
                        # Is it a sequence?
                        if len(
                            node['file'].value() or ''
                        ) and not os.path.splitext(node['file'].value())[
                            1
                        ].lower() in [
                            '.mov',
                            '.mxf',
                        ]:
                            file_node = node
                            break
                if file_node is None:
                    return (
                        False,
                        {'message': 'No sequence write node selected!'},
                    )
                self.logger.debug(
                    'Using existing node {} file sequence path: "{}", copying to temp.'.format(
                        file_node.name(), file_node['file'].value()
                    )
                )

                expression = '{} [{}-{}]'.format(
                    file_node['file'].value(),
                    int(file_node['first'].value()),
                    int(file_node['last'].value()),
                )

                collections = clique.parse(expression)

                temp_sequence_dir = tempfile.mkdtemp()
                if not os.path.exists(temp_sequence_dir):
                    os.makedirs(temp_sequence_dir)

                # Copy sequence
                for collection in collections:
                    source_path = str(collection)
                    destination_path = os.path.join(
                        temp_sequence_dir, os.path.basename(source_path)
                    )
                    self.logger.debug(
                        'Copying "{}" > "{}"'.format(
                            source_path, destination_path
                        )
                    )
                    shutil.copy(source_path, destination_path)

                sequence_path = '{} [{}-{}]'.format(
                    os.path.join(
                        temp_sequence_dir,
                        os.path.basename(file_node['file'].value()),
                    ),
                    int(file_node['first'].value()),
                    int(file_node['last'].value()),
                )
        finally:
            # restore selection
            nuke_utils.cleanSelection()
            for node in selected_nodes:
                node['selected'].setValue(True)

        return [str(sequence_path)]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeSequencePublisherExporterPlugin(api_object)
    plugin.register()
