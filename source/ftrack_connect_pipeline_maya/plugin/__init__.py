# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack
import maya

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_maya import constants as maya_constants
from ftrack_connect_pipeline_maya import utils as maya_utils
from ftrack_connect_pipeline_maya.asset import MayaFtrackObjectManager
from ftrack_connect_pipeline_maya.asset.dcc_object import MayaDccObject


class MayaBasePlugin(plugin.BasePlugin):
    host_type = maya_constants.HOST_TYPE

    FtrackObjectManager = MayaFtrackObjectManager
    '''FtrackObjectManager class to use'''
    DccObject = MayaDccObject
    '''DccObject class to use'''

    @maya_utils.run_in_main_thread
    def _run(self, event):
        return super(MayaBasePlugin, self)._run(event)


class MayaBasePluginWidget(MayaBasePlugin, pluginWidget.BasePluginWidget):
    category = 'plugin.widget'
    ui_type = maya_constants.UI_TYPE

    @maya_utils.run_in_main_thread
    def _run(self, event):
        return super(MayaBasePluginWidget, self)._run(event)


from ftrack_connect_pipeline_maya.plugin.load import *
from ftrack_connect_pipeline_maya.plugin.open import *
from ftrack_connect_pipeline_maya.plugin.publish import *
from ftrack_connect_pipeline_maya.plugin.asset_manager import *
