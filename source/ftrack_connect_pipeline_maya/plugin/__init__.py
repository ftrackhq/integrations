# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack
import maya

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_maya import constants as maya_constants
from ftrack_connect_pipeline_maya.utils import custom_commands as maya_utils

class BaseMayaPlugin(plugin.BasePlugin):
    host_type = maya_constants.HOST_TYPE

    @maya_utils.run_in_main_thread
    def _run(self, event):
        return super(BaseMayaPlugin, self)._run(event)


class BaseMayaPluginWidget(BaseMayaPlugin, pluginWidget.BasePluginWidget):
    category = 'plugin.widget'
    ui_type = maya_constants.UI_TYPE

    @maya_utils.run_in_main_thread
    def _run(self, event):
        return super(BaseMayaPluginWidget, self)._run(event)


from ftrack_connect_pipeline_maya.plugin.load import *
from ftrack_connect_pipeline_maya.plugin.publish import *
from ftrack_connect_pipeline_maya.plugin.asset_manager import *
