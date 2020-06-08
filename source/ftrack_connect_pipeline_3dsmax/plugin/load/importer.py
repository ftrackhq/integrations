# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_3dsmax.plugin import (
    BaseMaxPlugin, BaseMaxPluginWidget
)

from ftrack_connect_pipeline_3dsmax.utils import custom_commands as max_utils
from ftrack_connect_pipeline_3dsmax.utils import ftrack_asset_node
from ftrack_connect_pipeline_3dsmax.constants import asset as asset_const


class LoaderImporterMaxPlugin(plugin.LoaderImporterPlugin, BaseMaxPlugin):
    ''' Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''
    asset_node_type = ftrack_asset_node.FtrackAssetNode

    def _run(self, event):
        self.old_data = max_utils.get_current_scene_objects()
        self.logger.debug('Scene objects: {}'.format(len(self.old_data)))

        context = event['data']['settings']['context']
        self.logger.debug('Current context : {}'.format(context))

        data = event['data']['settings']['data']
        self.logger.debug('Current data : {}'.format(data))

        options = event['data']['settings']['options']
        self.logger.debug('Current options : {}'.format(options))

        super_result = super(LoaderImporterMaxPlugin, self)._run(event)

        asset_load_mode = options.get('load_mode')

        # TODO: check if not asset_load_mode, because what happend loading the seq for example
        if not asset_load_mode and asset_load_mode == asset_const.OPEN_MODE:
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
            'Checked differences between nodes before and after'
            ' inport : {}'.format(diff)
        )

        ftrack_node_class = self.get_asset_node(context, data, options)

        ftrack_node = ftrack_node_class.init_node()

        ftrack_node_class.connect_objects(diff)


class LoaderImporterMaxWidget(pluginWidget.LoaderImporterWidget, BaseMaxPluginWidget):
    ''' Class representing a Collector Widget

    .. note::

        _required_output a List
    '''

