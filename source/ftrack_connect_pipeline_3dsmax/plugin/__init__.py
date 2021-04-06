# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import pymxs
from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_3dsmax import constants as max_constants



class BaseMaxPlugin(plugin.BasePlugin):
    host_type = max_constants.HOST_TYPE

    def _run(self, event):
        super_fn = super(BaseMaxPlugin, self)._run
        result = super_fn(event)
        return result


class BaseMaxPluginWidget(BaseMaxPlugin, pluginWidget.BasePluginWidget):
    category = 'plugin.widget'
    ui_type = max_constants.UI_TYPE


from ftrack_connect_pipeline_3dsmax.plugin.load import *
from ftrack_connect_pipeline_3dsmax.plugin.publish import *
from ftrack_connect_pipeline_3dsmax.plugin.asset_manager import *
