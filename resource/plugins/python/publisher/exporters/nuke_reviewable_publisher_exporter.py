# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import tempfile
import os
import shutil

import ftrack_api

import nuke

from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils


class NukeReviewablePublisherExporterPlugin(
    plugin.NukePublisherExporterPlugin
):
    '''Nuke reviewable exporter plugin'''

    plugin_name = 'nuke_reviewable_publisher_exporter'

    def run(self, context_data=None, data=None, options=None):
        '''Export a reviewable video file from Nuke from collected node with *data* based on *options*'''

        collected_objects = []
        for collector in data:
            collected_objects.extend(collector['result'])

        node_name = collected_objects[0]
        input_node = nuke.toNode(node_name)
        selected_nodes = nuke.selectedNodes()
        nuke_utils.cleanSelection()

        try:
            mode = (options.get('mode') or 'render').lower()
            if mode == 'render' or mode == 'render_from_sequence':
                # Render a new reviewable from script, or
                # pickup a already rendered sequence and make movie out of that
                delete_read_node = delete_write_node = False
                read_node = write_node = None
                if mode == 'render_from_sequence':
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

                    read_node = nuke.createNode('Read')
                    read_node.setInput(0, input_node)
                    read_node['file'].fromUserText(file_node['file'].value())
                    read_node['first'].setValue(file_node['first'].value())
                    read_node['last'].setValue(file_node['first'].value())
                    read_node['colorspace'].setValue(
                        file_node['colorspace'].value()
                    )
                    input_node = read_node
                    delete_read_node = True
                else:
                    write_node = nuke.createNode('Write')
                    write_node.setInput(0, input_node)
                    # Get the input of the given write dcc_object.
                    input_node = write_node
                    delete_write_node = True

                # Generate exporters file name for mov.
                temp_review_mov_path = tempfile.NamedTemporaryFile(
                    delete=False, suffix='.mov'
                ).name

                first = str(int(nuke.root().knob('first_frame').value()))
                last = str(int(nuke.root().knob('last_frame').value()))

                # Create a new write_node.
                review_node = nuke.createNode('Write')
                review_node.setInput(0, input_node)
                review_node['file'].setValue(
                    temp_review_mov_path.replace('\\', '/')
                )
                file_type = options.get('file_type', 'mov')
                review_node['file_type'].setValue(file_type)
                codec = options.get('codec', 'mp4v')
                review_node[
                    'mov64_codec'
                    if file_type == 'mov'
                    else 'mxf_video_codec_knob'
                ].setValue(codec)

                if input_node['use_limit'].getValue():
                    review_node['use_limit'].setValue(True)

                    first = str(int(input_node['first'].getValue()))
                    last = str(int(input_node['last'].getValue()))

                    review_node['first'].setValue(int(first))
                    review_node['last'].setValue(int(last))

                self.logger.debug(
                    'Rendering reviewable movie {}-{}'.format(first, last)
                )
                ranges = nuke.FrameRanges('{}-{}'.format(first, last))
                nuke.render(review_node, ranges, continueOnError=True)

                # delete thumbnail network after render
                nuke.delete(review_node)

                # delete temporal read and write nodes
                if delete_read_node:
                    nuke.delete(read_node)
                if delete_write_node:
                    nuke.delete(write_node)

            else:
                # Find movie write/read node among selected nodes
                file_node = None
                for node in selected_nodes:
                    if node.Class() in ['Read', 'Write']:
                        # Is it a sequence?
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
                    'Using existing node {} movie path: "{}", copying to temp...'.format(
                        file_node.name(), file_node['file'].value()
                    )
                )
                # Make a copy of the file so it can be moved
                # Generate exporters file name for mov.
                temp_review_mov_path = tempfile.NamedTemporaryFile(
                    delete=False, suffix='.mov'
                ).name

                shutil.copy(file_node['file'].value(), temp_review_mov_path)

        finally:
            # restore selection
            nuke_utils.cleanSelection()
            for node in selected_nodes:
                node['selected'].setValue(True)

        return [temp_review_mov_path]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeReviewablePublisherExporterPlugin(api_object)
    plugin.register()
