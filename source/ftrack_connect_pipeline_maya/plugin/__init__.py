# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_maya import constants as maya_constants


class BaseMayaPlugin(plugin.BasePlugin):
    host = maya_constants.HOST

    def __init__(self, session):
        super(BaseMayaPlugin, self).__init__(session)
        import maya
        self.maya = maya

    def _run(self, event):
        super_fn = super(BaseMayaPlugin, self)._run
        result = self.maya.utils.executeInMainThreadWithResult(super_fn, event)
        return result


class BaseMayaPluginWidget(BaseMayaPlugin, pluginWidget.BasePluginWidget):
    type = 'widget'
    ui = maya_constants.UI


from ftrack_connect_pipeline_maya.plugin.load import *
from ftrack_connect_pipeline_maya.plugin.publish import *
from ftrack_connect_pipeline_maya.plugin.asset_manager import *
