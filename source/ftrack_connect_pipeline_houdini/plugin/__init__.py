# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_houdini import constants as houdini_constants
from ftrack_connect_pipeline_houdini.asset import HoudiniFtrackObjectManager
from ftrack_connect_pipeline_houdini.asset.dcc_object import HoudiniDccObject


class HoudiniBasePlugin(plugin.BasePlugin):
    host_type = houdini_constants.HOST_TYPE

    FtrackObjectManager = HoudiniFtrackObjectManager
    '''FtrackObjectManager class to use'''
    DccObject = HoudiniDccObject
    '''DccObject class to use'''


class HoudiniBasePluginWidget(
    HoudiniBasePlugin, pluginWidget.BasePluginWidget
):
    category = 'plugin.widget'
    ui_type = houdini_constants.UI_TYPE


from ftrack_connect_pipeline_houdini.plugin.load import *
from ftrack_connect_pipeline_houdini.plugin.publish import *
from ftrack_connect_pipeline_houdini.plugin.asset_manager import *
