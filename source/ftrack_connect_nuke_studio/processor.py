# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os
import nuke
import copy

import json
import tempfile

import FnAssetAPI
import assetmgr_hiero
import ftrack_connect_nuke_studio


def config():

    config = os.getenv('FTRACK_NUKE_STUDIO_CONFIG')
    if not config or not os.path.exists(config):
        FnAssetAPI.logging.error('please set FTRACK_NUKE_STUDIO_CONFIG environment variable to a valid json file')
        return

    data = json.load(file(config, 'r'))
    processors = data.get('processor')

    ftrack_connect_nuke_studio.setup()
    plugins = ftrack_connect_nuke_studio.PROCESSOR_PLUGINS

    def setup(node):
        ''' In Place replacement for processors in config'''

        for key, item in node.items():
            if isinstance(item, dict):
                setup(item)
            else:
                node[key] = plugins.get(item)

    setup(processors)
    return processors


def frame_range(trackItem, frames, handles):
    opts = {
        'numbering' : ('custom' ), # custom
        'customNumberingStart' : frames,
        'handles' : ('custom' ), # custom
        'customHandleLength' : handles,
        'includeRetiming' : True,
        'clampToPositive' : True
    }

    return assetmgr_hiero.utils.track.timingsFromTrackItem(trackItem, opts)



class BasePlugin(object):

    def __eq__(self, other):
        return self._name == other._name

    def __init__(self, name=None):
        self._defaults = {}
        self._name = name
        self._widget = None
        self._script = None

    def getName(self):
        # this is required for the plugin compatibility
        return self.name

    @property
    def defaults(self):
        return copy.deepcopy(self._defaults)

    @defaults.setter
    def defaults(self, data):
        self._defaults = data

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def script(self):
        return self._script

    @script.setter
    def script(self, script):
        script = os.path.expandvars(script)
        if not os.path.exists(script):
            FnAssetAPI.logging.error('%s does not exist' % script)

        self._script = script

    def _apply_options_to_nuke_script(self, values):
        for node_name, node_values in values.items():
            for kname, kvalue in node_values.items():
                node = nuke.toNode(node_name)
                try:
                    if kname == 'format':
                        f = nuke.addFormat(str(kvalue))
                        node[kname].setValue(f)
                    else:
                        node[kname].setValue(kvalue)
                except Exception as error:
                    FnAssetAPI.logging.debug('No knob %s on node %s: %s not applied' % (kname, node_name, kvalue))

    def _ensure_attributes(self, node):
        ''' Provide some common attiributes to the node.
        '''
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
        '''

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

        # update defaults
        result.get('IN', {}).update(self.defaults.get('IN', {}))
        result.get('OUT', {}).update(self.defaults.get('OUT', {}))
        result.get('REFORMAT', {}).update(self.defaults.get('REFORMAT',{}))
        result.get('OFFSET', {}).update(self.defaults.get('OFFSET',{}))
        result.get('root', {}).update(self.defaults.get('root',{}))
        return result

    def process(self, data):
        ''' Run the script with the given options.
        '''
        nuke.scriptClear()
        nuke.nodePaste(self.script)
        read_node = nuke.toNode('IN')
        write_node = nuke.toNode('OUT')

        if not all([read_node, write_node]):
            raise ValueError('The nuke script requires tho have an IN and an OUT node !')

        options = self.manage_options(data)
        self._ensure_attributes(write_node)
        self._apply_options_to_nuke_script(options)

        start = write_node['first'].value()
        end = write_node['last'].value()

        tmp = tempfile.NamedTemporaryFile(suffix='.nk', delete=False, prefix=self.getName())
        FnAssetAPI.logging.info('Saving tmp script to : %s' % tmp.name)
        nuke.scriptSaveAs(tmp.name)
        nuke.executeBackgroundNuke(
            nuke.EXE_PATH, [write_node],
            nuke.FrameRanges([nuke.FrameRange('%s-%s'%(int(start), int(end)))]),
            nuke.views(),
            {}
        )
        nuke.scriptClear()
