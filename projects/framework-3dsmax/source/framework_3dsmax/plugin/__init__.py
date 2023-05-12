# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from framework_core import plugin
from framework_qt import plugin as pluginWidget
from framework_3dsmax import constants as max_constants
from framework_3dsmax import utils as max_utils
from framework_3dsmax.asset import MaxFtrackObjectManager
from framework_3dsmax.asset.dcc_object import MaxDccObject


class MaxBasePlugin(plugin.BasePlugin):

    host_type = max_constants.HOST_TYPE

    FtrackObjectManager = MaxFtrackObjectManager
    '''FtrackObjectManager class to use'''
    DccObject = MaxDccObject
    '''DccObject class to use'''

    @max_utils.run_in_main_thread
    def _run(self, event):
        return super(MaxBasePlugin, self)._run(event)


class MaxBasePluginWidget(MaxBasePlugin, pluginWidget.BasePluginWidget):
    category = 'plugin.widget'
    ui_type = max_constants.UI_TYPE

    @max_utils.run_in_main_thread
    def _run(self, event):
        return super(MaxBasePluginWidget, self)._run(event)


from framework_3dsmax.plugin.load import *
from framework_3dsmax.plugin.open import *
from framework_3dsmax.plugin.publish import *
from framework_3dsmax.plugin.asset_manager import *
