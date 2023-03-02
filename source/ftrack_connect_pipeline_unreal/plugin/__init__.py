# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_connect_pipeline import plugin

from ftrack_connect_pipeline_qt import plugin as pluginWidget

from ftrack_connect_pipeline_unreal import constants as unreal_constants
from ftrack_connect_pipeline_unreal import utils as unreal_utils
from ftrack_connect_pipeline_unreal.asset import UnrealFtrackObjectManager
from ftrack_connect_pipeline_unreal.asset.dcc_object import UnrealDccObject


class UnrealBasePlugin(plugin.BasePlugin):
    host_type = unreal_constants.HOST_TYPE

    FtrackObjectManager = UnrealFtrackObjectManager
    '''FtrackObjectManager class to use'''
    DccObject = UnrealDccObject
    '''DccObject class to use'''

    @unreal_utils.run_in_main_thread
    def _run(self, event):
        return super(UnrealBasePlugin, self)._run(event)


class UnrealBasePluginWidget(UnrealBasePlugin, pluginWidget.BasePluginWidget):
    category = 'plugin.widget'
    ui_type = unreal_constants.UI_TYPE

    @unreal_utils.run_in_main_thread
    def _run(self, event):
        return super(UnrealBasePluginWidget, self)._run(event)


from ftrack_connect_pipeline_unreal.plugin.load import *
from ftrack_connect_pipeline_unreal.plugin.publish import *
from ftrack_connect_pipeline_unreal.plugin.asset_manager import *
