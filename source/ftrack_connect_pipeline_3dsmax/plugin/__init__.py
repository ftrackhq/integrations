# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import 3dsmax

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_3dsmax import constants as 3dsmax_constants
from ftrack_connect_pipeline_3dsmax.utils import custom_commands as 3dsmax_utils
from ftrack_connect_pipeline_3dsmax.asset import MaxFtrackObjectManager
from ftrack_connect_pipeline_3dsmax.asset.dcc_object import MaxDccObject


class MaxBasePlugin(plugin.BasePlugin):

    host_type = 3dsmax_constants.HOST_TYPE

    FtrackObjectManager = MaxFtrackObjectManager
    '''FtrackObjectManager class to use'''
    DccObject = MaxDccObject
    '''DccObject class to use'''

    @3dsmax_utils.run_in_main_thread
    def _run(self, event):
        return super(MaxBasePlugin, self)._run(event)


class MaxBasePluginWidget(MaxBasePlugin, pluginWidget.BasePluginWidget):
    category = 'plugin.widget'
    ui_type = 3dsmax_constants.UI_TYPE

    @3dsmax_utils.run_in_main_thread
    def _run(self, event):
        return super(MaxBasePluginWidget, self)._run(event)


from ftrack_connect_pipeline_3dsmax.plugin.load import *
from ftrack_connect_pipeline_3dsmax.plugin.open import *
from ftrack_connect_pipeline_3dsmax.plugin.publish import *
from ftrack_connect_pipeline_3dsmax.plugin.asset_manager import *
