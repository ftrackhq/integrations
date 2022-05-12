# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import nuke
from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_nuke import constants as nuke_constants
from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils
from ftrack_connect_pipeline_nuke.asset import NukeFtrackObjectManager
from ftrack_connect_pipeline_nuke.asset import NukeDccObject


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


from ftrack_connect_pipeline_nuke.plugin.load import *
from ftrack_connect_pipeline_nuke.plugin.open import *
from ftrack_connect_pipeline_nuke.plugin.publish import *
from ftrack_connect_pipeline_nuke.plugin.asset_manager import *
