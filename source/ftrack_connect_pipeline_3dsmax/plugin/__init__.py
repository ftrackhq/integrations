# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_3dsmax import constants as max_constants



class BaseMaxPlugin(plugin.BasePlugin):
    host = max_constants.HOST

    def _run(self, event):
        super_fn = super(BaseMaxPlugin, self)._run
        result = super_fn(event)
        return result


class BaseMaxPluginWidget(BaseMaxPlugin, pluginWidget.BasePluginWidget):
    type = 'widget'
    ui = max_constants.UI


from ftrack_connect_pipeline_3dsmax.plugin.load import *
from ftrack_connect_pipeline_3dsmax.plugin.publish import *
