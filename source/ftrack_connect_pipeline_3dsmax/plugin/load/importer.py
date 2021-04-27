# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import json
import six
import base64

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_3dsmax.plugin import (
    BaseMaxPlugin, BaseMaxPluginWidget
)

from ftrack_connect_pipeline_3dsmax.utils import custom_commands as max_utils
from ftrack_connect_pipeline_3dsmax.asset import FtrackAssetNode
from ftrack_connect_pipeline_3dsmax.constants.asset import modes as load_const
from ftrack_connect_pipeline_3dsmax.constants import asset as asset_const


class LoaderImporterMaxPlugin(plugin.LoaderImporterPlugin, BaseMaxPlugin):
    ''' Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''
    ftrack_asset_class = FtrackAssetNode

    def _run(self, event):
        self.old_data = max_utils.get_current_scene_objects()
        self.logger.debug('Scene objects: {}'.format(len(self.old_data)))

        super_result = super(LoaderImporterMaxPlugin, self)._run(event)

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

        asset_load_mode = options.get(asset_const.LOAD_MODE)

        if asset_load_mode == load_const.OPEN_MODE:
            return super_result

        self.new_data = max_utils.get_current_scene_objects()
        self.logger.debug(
            'Scene objects after load: {}'.format(len(self.new_data))
        )

        self.link_to_ftrack_node(context, data, options)

        return super_result

    def _get_difference(self, new_data, old_data):
        '''Returns the objects on on *new_data* that are not on the *old_data*

        ..note:: This function is for 3dmax only as can't compare the sets.
        '''
        #Re constructing the list as we can't compare the list coming from max
        old_data_list = [x for x in old_data]
        new_data_list = [x for x in new_data]
        diff = []
        for obj in new_data_list:
            if obj not in old_data_list:
                diff.append(obj)
        return diff

    def link_to_ftrack_node(self, context, data, options):
        diff = self._get_difference(self.new_data, self.old_data)

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


class LoaderImporterMaxWidget(pluginWidget.LoaderImporterWidget, BaseMaxPluginWidget):
    ''' Class representing a Collector Widget

    .. note::

        _required_output a List
    '''

