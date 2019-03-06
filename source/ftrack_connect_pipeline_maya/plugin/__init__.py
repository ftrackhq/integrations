# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline_maya import constants as maya_constants


class _BaseMaya(plugin._Base):
    host = maya_constants.HOST


class BaseMayaPlugin(plugin.BasePlugin, _BaseMaya):
    type = 'plugin'


class BaseMayaWidget(plugin.BaseWidget,_BaseMaya):
    type = 'widget'
    ui = maya_constants.UI


class ContextMayaPlugin(BaseMayaPlugin):
    plugin_type = constants.CONTEXT


class ContextMayaWidget(BaseMayaWidget):
    plugin_type = constants.CONTEXT


from ftrack_connect_pipeline_maya.plugin.load import *
from ftrack_connect_pipeline_maya.plugin.publish import *