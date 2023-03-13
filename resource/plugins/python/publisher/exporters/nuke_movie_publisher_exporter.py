# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import ftrack_api
import os
import clique
import tempfile
import shutil

from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_nuke import utils as nuke_utils

import nuke


class NukeMoviePublisherExporterPlugin(plugin.NukePublisherExporterPlugin):
    '''Nuke movie exporter plugin'''

    plugin_name = 'nuke_movie_publisher_exporter'

    def run(self, context_data=None, data=None, options=None):
        '''Export a video file from Nuke from collected node with *data* based on *options*'''

        node_name = None
        media_path = image_sequence_path = None
        create_write = False
        for collector in data:
            result = collector['result'][0]
            if 'node_name' in result:
                node_name = result['node_name']
                create_write = result.get('create_write', False)
            elif 'image_sequence_path' in result:
                image_sequence_path = result['image_sequence_path']
            else:
                media_path = result['media_path']
                render_from_image_sequence = result.get('render', False)

        if node_name:
            input_node = nuke.toNode(node_name)
            selected_nodes = nuke.selectedNodes()
            nuke_utils.clean_selection()

            try:
                if create_write:
                    # Create and render a write node and connect it to the selected input node
                    delete_write_node = True
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

                    first = int(write_node['first'].getValue())
                    last = int(write_node['last'].getValue())

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

                    self.logger.debug(
                        'Rendering movie [{}-{}] to "{}"'.format(
                            first, last, movie_path
                        )
                    )
                    nuke.render(write_node, first, last, continueOnError=True)

                    if delete_write_node:
                        # delete temporal write node
                        nuke.delete(write_node)

                else:
                    # Render the selected prepared write node
                    write_node = input_node
                    if not write_node.Class() == 'Write':
                        return (
                            False,
                            {'message': 'No write node selected!'},
                        )

                    file_path = write_node['file'].value()
                    if file_path is None or not (
                        file_path.lower().endswith('.mov')
                        or file_path.lower().endswith('.mxf')
                    ):
                        return (
                            False,
                            {'message': 'No movie write node selected!'},
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

                    selected_file_format = str(options.get('file_format'))

                    restore_file_path = False
                    try:
                        if options.get('to_temp'):
                            restore_file_path = write_node['file'].getValue()

                            temp_name = tempfile.NamedTemporaryFile()

                            movie_path = '{}.{}'.format(
                                temp_name.name, selected_file_format
                            )
                            write_node['file'].setValue(
                                movie_path.replace('\\', '/')
                            )

                        else:
                            movie_path = file_path

                        write_node['file_type'].setValue(selected_file_format)
                        # Set additional file format options
                        # TODO: Document macOs crash and how to choose mp4v codec if mov file format as a work around
                        if len(options.get(selected_file_format) or {}) > 0:
                            for k, v in options[selected_file_format].items():
                                if k not in ['codecs', 'codec_knob_name']:
                                    write_node[k].setValue(v)

                        self.logger.debug(
                            'Rendering movie [{}-{}] from selected write node "{}" to "{}"'.format(
                                first, last, write_node['name'], movie_path
                            )
                        )
                        nuke.render(
                            write_node, first, last, continueOnError=True
                        )
                    finally:
                        # Restore temp render path if needed
                        if restore_file_path:
                            write_node['file'].setValue(restore_file_path)
            finally:
                # restore selection
                nuke_utils.clean_selection()
                for node in selected_nodes:
                    node['selected'].setValue(True)
        else:
            if image_sequence_path:
                # Expected an image sequence supplied, render movie from it
                delete_read_node = False
                # Read the sequence
                collection = clique.parse(image_sequence_path)

                read_node = nuke.createNode('Read')
                delete_read_node = True
                read_node['file'].fromUserText(
                    collection.format('{head}{padding}{tail}')
                )
                first = list(collection.indexes)[0]
                last = list(collection.indexes)[-1]
                read_node['first'].setValue(first)
                read_node['last'].setValue(last)

                write_node = nuke.createNode('Write')
                delete_write_node = True
                write_node.setInput(0, read_node)

                write_node['first'].setValue(first)
                write_node['last'].setValue(last)

                selected_file_format = str(options.get('file_format'))

                # Generate exporters file name for mov.
                temp_name = tempfile.NamedTemporaryFile()

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

                self.logger.debug(
                    'Rendering movie [{}-{}] from image sequence "{}" to "{}"'.format(
                        first, last, image_sequence_path, movie_path
                    )
                )
                nuke.render(write_node, first, last, continueOnError=True)

                if delete_write_node:
                    # delete temporal write node
                    nuke.delete(write_node)

                if delete_read_node:
                    nuke.delete(read_node)

            else:
                if options.get('to_temp'):
                    self.logger.debug(
                        'Picking up rendered file movie and copying to temp for publish: "{}"'.format(
                            media_path
                        )
                    )
                    temp_name = tempfile.NamedTemporaryFile(
                        suffix=os.path.splitext(media_path)[-1]
                    ).name
                    shutil.copy(media_path, temp_name)
                    media_path = temp_name
                else:
                    self.logger.debug(
                        'Picking up rendered file movie for publish: "{}"'.format(
                            media_path
                        )
                    )
                movie_path = media_path

        return [str(movie_path)]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeMoviePublisherExporterPlugin(api_object)
    plugin.register()
