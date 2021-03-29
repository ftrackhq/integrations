# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import json
import six
import base64

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_maya.plugin import (
    BaseMayaPlugin, BaseMayaPluginWidget
)

from ftrack_connect_pipeline_maya.utils import custom_commands as maya_utils
from ftrack_connect_pipeline_maya.asset import FtrackAssetNode
from ftrack_connect_pipeline_maya.constants.asset import modes as load_const
from ftrack_connect_pipeline_maya.constants import asset as asset_const

class LoaderImporterMayaPlugin(plugin.LoaderImporterPlugin, BaseMayaPlugin):
    ''' Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''
    ftrack_asset_class = FtrackAssetNode

    def _run(self, event):

        self.old_data = maya_utils.get_current_scene_objects()
        self.logger.debug('Scene objects : {}'.format(len(self.old_data)))

        super_result = super(LoaderImporterMayaPlugin, self)._run(event)

        context = self.plugin_settings.get('context')
        self.logger.debug('Current context : {}'.format(context))

        data = self.plugin_settings.get('data')
        self.logger.debug('Current data : {}'.format(data))

        options = self.plugin_settings.get('options')
        self.logger.debug('Current options : {}'.format(options))

        json_data = json.dumps(event['data'])
        if six.PY2:
            options[asset_const.ASSET_INFO_OPTIONS] = base64.b64encode(
                json_data
            )
        else:
            input_bytes = json_data.encode('utf8')
            options[asset_const.ASSET_INFO_OPTIONS] = base64.b64encode(
                input_bytes
            ).decode('ascii')

        asset_load_mode = options.get(asset_const.LOAD_MODE, 'Not set')

        if asset_load_mode == load_const.OPEN_MODE:
            self.logger.warning('{} not created, load mode is {} and not {}'.format(
                self.ftrack_asset_class, asset_load_mode, load_const.OPEN_MODE))
            return super_result

        self.new_data = maya_utils.get_current_scene_objects()
        self.logger.debug(
            'Scene objects after load : {}'.format(len(self.new_data))
        )

        self.link_to_ftrack_node(context, data, options)

        return super_result

    def link_to_ftrack_node(self, context, data, options):
        diff = self.new_data.difference(self.old_data)
        if not diff:
            self.logger.debug('No differences found in the scene')
            return

        self.logger.debug(
            'Checked differences between ftrack_objects before and after'
            ' inport : {}'.format(diff)
        )

        ftrack_asset_class = self.get_asset_class(context, data, options)

        ftrack_node = ftrack_asset_class.init_ftrack_object()
        ftrack_asset_class.connect_objects(diff)



class LoaderImporterMayaWidget(pluginWidget.LoaderImporterWidget, BaseMayaPluginWidget):
    ''' Class representing a Collector Widget

    .. note::

        _required_output a List
    '''

