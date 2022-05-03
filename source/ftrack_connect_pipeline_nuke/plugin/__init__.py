# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import nuke
from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_nuke import constants as nuke_constants
from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils
from ftrack_connect_pipeline_nuke.asset import NukeFtrackObjectManager as FtrackObjectManager
from ftrack_connect_pipeline_nuke.asset import NukeDccObject as DccObject


class BaseNukePlugin(plugin.BasePlugin):
    host_type = nuke_constants.HOST_TYPE

    @property
    def ftrack_object_manager(self):
        '''
        Initializes and returns the FtrackObjectManager class
        '''
        if not isinstance(self._ftrack_object_manager, FtrackObjectManager):
            self._ftrack_object_manager = FtrackObjectManager(self.event_manager)
        return self._ftrack_object_manager

    @property
    def DccObject(self):
        '''
        Returns the not initialized DccObject class
        '''
        # We can not pre-initialize this because should be a new
        # one each time we want to use it.
        self._DccObject = DccObject
        return self._DccObject

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
from ftrack_connect_pipeline_nuke.plugin.open import *
from ftrack_connect_pipeline_nuke.plugin.publish import *
from ftrack_connect_pipeline_nuke.plugin.asset_manager import *
