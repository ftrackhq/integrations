# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import nuke
from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_nuke import constants as nuke_constants
from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils


class BaseNukePlugin(plugin.BasePlugin):
    host_type = nuke_constants.HOST_TYPE

    @nuke_utils.run_in_main_thread
    def _run(self, event):
        super_fn = super(BaseNukePlugin, self)._run
        result = super_fn(event)
        return result


class BaseNukePluginWidget(BaseNukePlugin, pluginWidget.BasePluginWidget):
    ui_type = nuke_constants.UI_TYPE

    @nuke_utils.run_in_main_thread
    def _run(self, event):
        super_fn = super(BaseNukePluginWidget, self)._run
        result = super_fn(event)
        return result


from ftrack_connect_pipeline_nuke.plugin.load import *
from ftrack_connect_pipeline_nuke.plugin.publish import *
from ftrack_connect_pipeline_nuke.plugin.asset_manager import *
