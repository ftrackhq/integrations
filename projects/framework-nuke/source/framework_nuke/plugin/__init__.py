# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import nuke
from framework_core import plugin
from framework_qt import plugin as pluginWidget
from framework_nuke import constants as nuke_constants
from framework_nuke import utils as nuke_utils
from framework_nuke.asset import NukeFtrackObjectManager
from framework_nuke.asset import NukeDccObject


class NukeBasePlugin(plugin.BasePlugin):
    host_type = nuke_constants.HOST_TYPE

    FtrackObjectManager = NukeFtrackObjectManager
    '''FtrackObjectManager class to use'''
    DccObject = NukeDccObject
    '''DccObject class to use'''

    @nuke_utils.run_in_main_thread
    def _run(self, event):
        super_fn = super(NukeBasePlugin, self)._run
        result = super_fn(event)
        return result


class NukeBasePluginWidget(NukeBasePlugin, pluginWidget.BasePluginWidget):
    ui_type = nuke_constants.UI_TYPE

    @nuke_utils.run_in_main_thread
    def _run(self, event):
        super_fn = super(NukeBasePluginWidget, self)._run
        result = super_fn(event)
        return result


from framework_nuke.plugin.load import *
from framework_nuke.plugin.open import *
from framework_nuke.plugin.publish import *
from framework_nuke.plugin.asset_manager import *
