# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_houdini import constants as houdini_constants


class BaseHoudiniPlugin(plugin.BasePlugin):
    host_type = houdini_constants.HOST_TYPE
    ''' '''


class BaseHoudiniPluginWidget(BaseHoudiniPlugin, pluginWidget.BasePluginWidget):
    category = 'plugin.widget'
    ui_type = houdini_constants.UI_TYPE


from ftrack_connect_pipeline_houdini.plugin.load import *
from ftrack_connect_pipeline_houdini.plugin.publish import *
from ftrack_connect_pipeline_houdini.plugin.asset_manager import *
