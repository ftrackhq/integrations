# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline_nuke import constants as nuke_constants


class _Basenuke(plugin._Base):
    host = nuke_constants.HOST


class BasenukePlugin(plugin.BasePlugin, _Basenuke):
    type = 'plugin'


class BasenukeWidget(plugin.BaseWidget,_Basenuke):
    type = 'widget'
    ui = nuke_constants.UI


class ContextnukePlugin(BasenukePlugin):
    plugin_type = constants.CONTEXT


class ContextnukeWidget(BasenukeWidget):
    plugin_type = constants.CONTEXT


from ftrack_connect_pipeline_nuke.plugin.load import *
from ftrack_connect_pipeline_nuke.plugin.publish import *