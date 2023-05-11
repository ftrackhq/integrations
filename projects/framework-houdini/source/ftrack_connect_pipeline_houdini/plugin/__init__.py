# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_houdini import constants as houdini_constants
from ftrack_connect_pipeline_houdini.asset import HoudiniFtrackObjectManager
from ftrack_connect_pipeline_houdini.asset.dcc_object import HoudiniDccObject
from ftrack_connect_pipeline_houdini import utils as houdini_utils


class HoudiniBasePlugin(plugin.BasePlugin):
    host_type = houdini_constants.HOST_TYPE

    FtrackObjectManager = HoudiniFtrackObjectManager
    '''FtrackObjectManager class to use'''
    DccObject = HoudiniDccObject
    '''DccObject class to use'''

    @houdini_utils.run_in_main_thread
    def _run(self, event):
        return super(HoudiniBasePlugin, self)._run(event)


class HoudiniBasePluginWidget(
    HoudiniBasePlugin, pluginWidget.BasePluginWidget
):
    category = 'plugin.widget'
    ui_type = houdini_constants.UI_TYPE

    @houdini_utils.run_in_main_thread
    def _run(self, event):
        return super(HoudiniBasePluginWidget, self)._run(event)


from ftrack_connect_pipeline_houdini.plugin.load import *
from ftrack_connect_pipeline_houdini.plugin.open import *
from ftrack_connect_pipeline_houdini.plugin.publish import *
from ftrack_connect_pipeline_houdini.plugin.asset_manager import *
