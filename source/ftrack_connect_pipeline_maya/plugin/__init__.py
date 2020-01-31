# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import maya
from ftrack_connect_pipeline import exception
from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_maya import constants as maya_constants



class BaseMayaPlugin(plugin.BasePlugin):
    host = maya_constants.HOST

    def _run(self, event):
        super_fn = super(BaseMayaPlugin, self)._run
        result = maya.utils.executeInMainThreadWithResult(super_fn, event)
        return result


# class BaseMayaPlugin(plugin.BasePlugin, _BaseMaya):
#     type = 'plugin'


class BaseMayaPluginWidget(BaseMayaPlugin, pluginWidget.BasePluginWidget):
    type = 'widget'
    ui = maya_constants.UI


from ftrack_connect_pipeline_maya.plugin.collector import *
from ftrack_connect_pipeline_maya.plugin.context import *
from ftrack_connect_pipeline_maya.plugin.finaliser import *
from ftrack_connect_pipeline_maya.plugin.output import *
from ftrack_connect_pipeline_maya.plugin.validator import *
