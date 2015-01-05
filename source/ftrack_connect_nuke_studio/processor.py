# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

from __future__ import absolute_import

import os
import json
import tempfile
import logging

import nuke
import FnAssetAPI

import ftrack_connect_nuke_studio


def config():
    '''Configure processors.'''
    config = os.getenv('FTRACK_NUKE_STUDIO_CONFIG')
    if not config or not os.path.exists(config):
        FnAssetAPI.logging.error(
            'FTRACK_NUKE_STUDIO_CONFIG environment variable not set. No '
            'processor plugins will be configured.'
        )
        return

    data = json.load(file(config, 'r'))
    processors = data.get('processor')

    ftrack_connect_nuke_studio.setup()
    plugins = ftrack_connect_nuke_studio.PROCESSOR_PLUGINS

    def setup(node):
        ''' In-place replacement for processors in config'''
        for key, item in node.items():
            if isinstance(item, dict):
                setup(item)
            else:
                plugin = plugins.get(item)
                if plugin is None:
                    FnAssetAPI.logging.debug(
                        'No processor plugin found with name "{0}"'.format(item)
                    )
                else:
                    node[key] = plugin

    setup(processors)
    return processors


class ProcessorPlugin(object):
    '''Processor plugin.'''

    def __init__(self):
        '''Initialise processor plugin.'''
        self.name = 'processor.base'
        self.defaults = {}
        self.script = None
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

    def __eq__(self, other):
        '''Return whether this plugin is the same as *other*.'''
        return self.name == other.name

    def getName(self):
        '''Return unique name of plugin.'''
        return self.name

    def _apply_options_to_nuke_script(self, options):
        '''Apply *options* to nuke script.'''
        for node_name, node_values in options.items():
            for knob_name, knob_value in node_values.items():
                node = nuke.toNode(node_name)

                try:
                    if knob_name == 'format':
                        format = nuke.addFormat(str(knob_value))
                        node[knob_name].setValue(format)
                    else:
                        node[knob_name].setValue(knob_value)

                except Exception:
                    self.logger.debug(
                        'No knob {0} on node {1}: {2} not applied.'.format(
                            knob_name, node_name, knob_value
                        )
                    )

    def _ensure_attributes(self, node):
        '''Ensure standard attributes set on *node*.'''
        asset_version_id = 'asset_version_id'
        component_name = 'component_name'
        node_knobs = node.knobs()

        if asset_version_id not in node_knobs:
            reference_data = nuke.String_Knob('asset_version_id')
            node.addKnob(reference_data)

        if component_name not in node_knobs:
            component_name = nuke.String_Knob('component_name')
            node.addKnob(component_name)

    def prepare_data(self, data):
        '''Return data mapping processed from input *data*.

        *data* is a dictionary containing data for generating the final
        output. this function is expected to return a dictionary within this
        format: {<NODE_NAME >:{<KNOB_NAME>:<VALUE>}}

        The available keys of data are:

        - resolution
        - source_in
        - source_out
        - source_file
        - time_offset
        - destination_in
        - destination_out
        - handles
        - fps
        - asset_version_id
        - component_name

        '''
        options = {
            'IN': {
                'first': int(data['source_in']) - int(data['handles']),
                'last': int(data['source_out']) + int(data['handles']),
                'file': data['source_file']
            },
            'OUT': {
                'first': int(data['destination_in']),
                'last': int(data['destination_out']),
                'component_name': data['component_name'],
                'asset_version_id': data['asset_version_id'],
                'use_limit': True
            },
            'REFORMAT': {
                'output_format': data['resolution']
            },
            'OFFSET': {
                'time_offset': int(data['time_offset'])
            },
            'root': {
                'first_frame': int(data['destination_in']),
                'last_frame': int(data['destination_out']),
                'fps': int(data['fps'])
            }
        }

        # Update defaults
        options.get('IN', {}).update(self.defaults.get('IN', {}))
        options.get('OUT', {}).update(self.defaults.get('OUT', {}))
        options.get('REFORMAT', {}).update(self.defaults.get('REFORMAT', {}))
        options.get('OFFSET', {}).update(self.defaults.get('OFFSET', {}))
        options.get('root', {}).update(self.defaults.get('root', {}))

        return options

    def process(self, data):
        '''Run script against *data*.'''
        nuke.scriptClear()
        nuke.nodePaste(os.path.expandvars(self.script))
        read_node = nuke.toNode('IN')
        write_node = nuke.toNode('OUT')

        if not all([read_node, write_node]):
            raise ValueError(
                'Missing required IN and OUT nodes.'
            )

        self.logger.debug('Raw data: {0}'.format(data))
        data = self.prepare_data(data)
        self.logger.debug('Prepared data: {0}'.format(data))

        self._ensure_attributes(write_node)
        self._apply_options_to_nuke_script(data)

        start = write_node['first'].value()
        end = write_node['last'].value()

        temporary_script = tempfile.NamedTemporaryFile(
            suffix='.nk', delete=False, prefix=self.getName()
        )
        self.logger.info(
            'Saving temporary script to "{0}"'.format(temporary_script.name)
        )
        nuke.scriptSaveAs(temporary_script.name)

        nuke.executeBackgroundNuke(
            nuke.EXE_PATH,
            [write_node],
            nuke.FrameRanges([
                nuke.FrameRange('{0}-{1}'.format(int(start), int(end)))
            ]),
            nuke.views(),
            {}
        )
        nuke.scriptClear()
