# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_harmony import constants as harmony_constants
from ftrack_connect_pipeline_harmony import utils as harmony_utils
from ftrack_connect_pipeline_harmony.asset import HarmonyFtrackObjectManager
from ftrack_connect_pipeline_harmony.asset.dcc_object import HarmonyDccObject


class HarmonyBasePlugin(plugin.BasePlugin):

    host_type = harmony_constants.HOST_TYPE

    FtrackObjectManager = HarmonyFtrackObjectManager
    '''FtrackObjectManager class to use'''
    DccObject = HarmonyDccObject
    '''DccObject class to use'''

    @harmony_utils.run_in_main_thread
    def _run(self, event):
        return super(HarmonyBasePlugin, self)._run(event)


class HarmonyBasePluginWidget(HarmonyBasePlugin, pluginWidget.BasePluginWidget):
    category = 'plugin.widget'
    ui_type = harmony_constants.UI_TYPE

    @harmony_utils.run_in_main_thread
    def _run(self, event):
        return super(HarmonyBasePluginWidget, self)._run(event)


from ftrack_connect_pipeline_harmony.plugin.load import *
from ftrack_connect_pipeline_harmony.plugin.open import *
from ftrack_connect_pipeline_harmony.plugin.publish import *
from ftrack_connect_pipeline_harmony.plugin.asset_manager import *
