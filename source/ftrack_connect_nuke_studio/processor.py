# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os
import copy
import json
import tempfile

import nuke
import FnAssetAPI
import assetmgr_hiero

import ftrack_connect_nuke_studio


def config():
    '''Configure processors.'''
    config = os.getenv('FTRACK_NUKE_STUDIO_CONFIG')
    if not config or not os.path.exists(config):
        FnAssetAPI.logging.error(
            'FTRACK_NUKE_STUDIO_CONFIG environment variable must be set and '
            'point to a valid json file'
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
                node[key] = plugins.get(item)

    setup(processors)
    return processors


def frame_range(track_item, frames, handles):
    '''Return frame range for *track_item*.'''
    opts = {
        'numbering': 'custom',
        'customNumberingStart': frames,
        'handles': 'custom',
        'customHandleLength': handles,
        'includeRetiming': True,
        'clampToPositive': True
    }

    return assetmgr_hiero.utils.track.timingsFromTrackItem(track_item, opts)


class ProcessorPlugin(object):
    '''Processor plugin.'''

    def __init__(self, name=None):
        '''Initialise processor plugin.'''
        self.name = name
        self._defaults = {}
        self._script = None

    def __eq__(self, other):
        '''Return whether this plugin is the same as *other*.'''
        return self.name == other.name

    def getName(self):
        '''Return unique name of plugin.'''
        return self.name

    @property
    def defaults(self):
        '''Return defaults.'''
        return copy.deepcopy(self._defaults)

    @defaults.setter
    def defaults(self, defaults):
        '''Set *defaults*.'''
        self._defaults = defaults

    @property
    def script(self):
        '''Return script.'''
        return self._script

    @script.setter
    def script(self, script):
        '''Set *script*.

        *script* must exist on disk.

        '''
        script = os.path.expandvars(script)
        if not os.path.exists(script):
            FnAssetAPI.logging.error('{0} does not exist'.format(script))

        self._script = script

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
                    FnAssetAPI.logging.debug(
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

    def manage_options(self, data):
        '''Return mapping to pass to script using input *data*.

        *data* is a dictionary containing data for generating the final output.
        this function is expected to return a dictioary within this format:
        {<NODE_NAME >:{<KNOB_NAME>:<VALUE>}}

        the available keys of data are:

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
        result = {
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
        result.get('IN', {}).update(self.defaults.get('IN', {}))
        result.get('OUT', {}).update(self.defaults.get('OUT', {}))
        result.get('REFORMAT', {}).update(self.defaults.get('REFORMAT', {}))
        result.get('OFFSET', {}).update(self.defaults.get('OFFSET', {}))
        result.get('root', {}).update(self.defaults.get('root', {}))

        return result

    def process(self, data):
        '''Run script against *data*.'''
        nuke.scriptClear()
        nuke.nodePaste(self.script)
        read_node = nuke.toNode('IN')
        write_node = nuke.toNode('OUT')

        if not all([read_node, write_node]):
            raise ValueError(
                'Missing required IN and OUT nodes.'
            )

        options = self.manage_options(data)
        self._ensure_attributes(write_node)
        self._apply_options_to_nuke_script(options)

        start = write_node['first'].value()
        end = write_node['last'].value()

        temporary_script = tempfile.NamedTemporaryFile(
            suffix='.nk', delete=False, prefix=self.getName()
        )
        FnAssetAPI.logging.info(
            'Saving temporary script to "{0}"'.format(temporary_script.name)
        )
        nuke.scriptSaveAs(temporary_script.name)

        nuke.executeBackgroundNuke(
            nuke.EXE_PATH,
            [write_node],
            nuke.FrameRanges([
                nuke.FrameRange('{0:d}-{1:d}'.format(start, end))
            ]),
            nuke.views(),
            {}
        )
        nuke.scriptClear()
