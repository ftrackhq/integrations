# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

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
    asset_node_type = FtrackAssetNode

    def _run(self, event):

        self.old_data = maya_utils.get_current_scene_objects()
        self.logger.debug('Scene objects : {}'.format(len(self.old_data)))

        context = event['data']['settings']['context']
        self.logger.debug('Current context : {}'.format(context))

        data = event['data']['settings']['data']
        self.logger.debug('Current data : {}'.format(data))

        options = event['data']['settings']['options']
        self.logger.debug('Current options : {}'.format(options))

        super_result = super(LoaderImporterMayaPlugin, self)._run(event)

        print "options before---> {}".format(options)
        print "event['data']---> {}".format(event['data'])
        print "event['data'].type()---> {}".format(event['data'])

        options.setdefault(asset_const.ASSET_INFO_OPTIONS, event['data'])
        # options[asset_const.ASSET_INFO_OPTIONS] = event['data']
        print "options after---> {}".format(options)


        asset_load_mode = options.get(asset_const.LOAD_MODE)

        if not asset_load_mode or asset_load_mode == load_const.OPEN_MODE:
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
            'Checked differences between nodes before and after'
            ' inport : {}'.format(diff)
        )

        ftrack_node_class = self.get_asset_node(context, data, options)

        ftrack_node = ftrack_node_class.init_node()

        ftrack_node_class.connect_objects(diff)



class LoaderImporterMayaWidget(pluginWidget.LoaderImporterWidget, BaseMayaPluginWidget):
    ''' Class representing a Collector Widget

    .. note::

        _required_output a List
    '''

