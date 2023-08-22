# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_core import plugin
from ftrack_framework_qt import plugin as pluginWidget
from ftrack_framework_houdini import constants as houdini_constants
from ftrack_framework_houdini.asset import HoudiniFtrackObjectManager
from ftrack_framework_houdini.asset.dcc_object import HoudiniDccObject
from ftrack_framework_houdini import utils as houdini_utils


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


from ftrack_framework_houdini.plugin.load import *
from ftrack_framework_houdini.plugin.open import *
from ftrack_framework_houdini.plugin.publish import *
from ftrack_framework_houdini.plugin.asset_manager import *
from ftrack_framework_houdini.plugin.resolver import *
