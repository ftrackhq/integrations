# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import ftrack_api
import os
import clique
import tempfile
import shutil

from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils

import nuke


class NukeMoviePublisherExporterPlugin(plugin.NukePublisherExporterPlugin):
    '''Nuke movie exporter plugin'''

    plugin_name = 'nuke_movie_publisher_exporter'

    def run(self, context_data=None, data=None, options=None):
        '''Export a video file from Nuke from collected node with *data* based on *options*'''

        collected_objects = []
        for collector in data:
            collected_objects.extend(collector['result'])

        node_name = collected_objects[0]
        input_node = nuke.toNode(node_name)
        selected_nodes = nuke.selectedNodes()
        nuke_utils.cleanSelection()

        try:
            mode = (options.get('mode') or 'render').lower()
            if mode in ['render', 'render_from_sequence']:
                write_node = read_node = None
                delete_write_node = True
                delete_read_node = False
                if mode == 'render_from_sequence':
                    # Find sequence read/write node
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
                            {
                                'message': 'No sequence write/read node selected!'
                            },
                        )
                    self.logger.debug(
                        'Using existing node {} file sequence path: "{}"'.format(
                            file_node.name(), file_node['file'].value()
                        )
                    )
                    if file_node.Class() in ['Write']:
                        # Read the sequence
                        read_node = nuke.createNode('Read')
                        read_node.setInput(0, input_node)
                        read_node['file'].fromUserText(
                            file_node['file'].value()
                        )
                        read_node['first'].setValue(file_node['first'].value())
                        read_node['last'].setValue(file_node['first'].value())
                        read_node['colorspace'].setValue(
                            file_node['colorspace'].value()
                        )
                        input_node = read_node
                        delete_read_node = True
                    else:
                        read_node = (
                            input_node
                        ) = file_node  # Use this read node during render
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

                selected_file_format = str(options.get('file_format'))

                # Generate exporters file name for mov.
                temp_name = tempfile.NamedTemporaryFile()

                first = str(int(write_node['first'].getValue()))
                last = str(int(write_node['last'].getValue()))

                movie_path = '{}.{}'.format(
                    temp_name.name, selected_file_format
                )

                write_node['file'].setValue(movie_path.replace('\\', '/'))

                write_node['file_type'].setValue(selected_file_format)
                # Set additional file format options
                # TODO: Document macOs crash and how to choose mp4v codec if mov file format as a work around
                if len(options.get(selected_file_format) or {}) > 0:
                    for k, v in options[selected_file_format].items():
                        if k not in ['codecs', 'codec_knob_name']:
                            write_node[k].setValue(v)

                ranges = nuke.FrameRanges('{}-{}'.format(first, last))
                self.logger.debug(
                    'Rendering movie [{}-{}] to "{}"'.format(
                        first, last, movie_path
                    )
                )
                nuke.render(write_node, ranges, continueOnError=True)

                if delete_write_node:
                    # delete temporal write node
                    nuke.delete(write_node)
                if delete_read_node:
                    nuke.delete(read_node)
            elif mode in ['render_write']:
                # Find movie write node among selected nodes
                write_node = None
                for node in selected_nodes:
                    if node.Class() in ['Write']:
                        # Is it a movie?
                        if len(
                            node['file'].value() or ''
                        ) and os.path.splitext(node['file'].value())[
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
                        {'message': 'No movie write/read node selected!'},
                    )
                first = str(int(write_node['first'].getValue()))
                last = str(int(write_node['last'].getValue()))

                ranges = nuke.FrameRanges('{}-{}'.format(first, last))
                movie_path = write_node['file'].value()

                self.logger.debug(
                    'Rendering movie [{}-{}] to "{}"'.format(
                        first, last, movie_path
                    )
                )
                nuke.render(write_node, ranges, continueOnError=True)

            else:
                # Find movie write/read node among selected nodes
                file_node = None
                for node in selected_nodes:
                    if node.Class() in ['Read', 'Write']:
                        # Is it a movie?
                        if len(
                            node['file'].value() or ''
                        ) and os.path.splitext(node['file'].value())[
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
                        {'message': 'No movie write/read node selected!'},
                    )
                self.logger.debug(
                    'Using existing node {} movie path: "{}", copying to temp.'.format(
                        file_node.name(), file_node['file'].value()
                    )
                )

                # Make a copy of the file so it can be moved
                # Generate exporters file name for mov.
                movie_path = tempfile.NamedTemporaryFile(
                    delete=False, suffix='.mov'
                ).name

                shutil.copy(file_node['file'].value(), movie_path)

        finally:
            # restore selection
            nuke_utils.cleanSelection()
            for node in selected_nodes:
                node['selected'].setValue(True)

        return [str(movie_path)]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeMoviePublisherExporterPlugin(api_object)
    plugin.register()
