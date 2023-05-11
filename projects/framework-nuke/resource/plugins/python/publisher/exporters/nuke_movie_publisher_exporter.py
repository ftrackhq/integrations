# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import ftrack_api
import os
import clique
import tempfile
import shutil

from framework_nuke import plugin
from framework_nuke import utils as nuke_utils

import nuke


class NukeMoviePublisherExporterPlugin(plugin.NukePublisherExporterPlugin):
    '''Nuke movie exporter plugin'''

    plugin_name = 'nuke_movie_publisher_exporter'

    def run(self, context_data=None, data=None, options=None):
        '''Export a video file from Nuke from collected node or supplied media
        with supplied *data* based on *options*'''

        node_name = None
        movie_path = image_sequence_path = None
        create_write = False
        for collector in data:
            result = collector['result'][0]
            if 'node_name' in result:
                node_name = result['node_name']
                create_write = result.get('create_write', False)
            elif 'image_sequence_path' in result:
                image_sequence_path = result['image_sequence_path']
            else:
                movie_path = result['movie_path']

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

                    self._apply_movie_file_format_options(write_node, options)

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
                    if not file_path or not os.path.splitext(
                        file_path.lower()
                    )[-1] in ['.mov', '.mxf', '.avi', '.r3d']:
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

                    if options.get('to_temp'):
                        # A reviewable movie needs to be rendered to temp location, as it is removed by framework
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

                    self._apply_movie_file_format_options(write_node, options)

                    self.logger.debug(
                        'Rendering movie [{}-{}] from selected write node "{}" to "{}"'.format(
                            first, last, write_node['name'], movie_path
                        )
                    )
                    nuke.render(write_node, first, last, continueOnError=True)

                    # Restore temp render path if needed
                    if restore_file_path:
                        write_node['file'].setValue(restore_file_path)
            except Exception as e:
                self.logger.error(e)
                return False, {'message': 'Movie render failed: '.format(e)}
            finally:
                # restore selection
                nuke_utils.clean_selection()
                for node in selected_nodes:
                    node['selected'].setValue(True)
        else:
            if image_sequence_path:
                # Expected an image sequence supplied, render movie from it
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

                self._apply_movie_file_format_options(write_node, options)

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
                    # A reviewable movie needs to be copied to temp location, as it is removed by framework
                    self.logger.debug(
                        'Picking up rendered file movie and copying to temp for publish: "{}"'.format(
                            movie_path
                        )
                    )
                    temp_name = tempfile.NamedTemporaryFile(
                        suffix=os.path.splitext(movie_path)[-1]
                    ).name
                    shutil.copy(movie_path, temp_name)
                    movie_path = temp_name
                else:
                    self.logger.debug(
                        'Picking up rendered file movie for publish: "{}"'.format(
                            movie_path
                        )
                    )

        return [str(movie_path)]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeMoviePublisherExporterPlugin(api_object)
    plugin.register()
