# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

# import sys
# import re
# import glob
# import os
# import traceback
# from ftrack_connect_pipeline import constants

import nuke

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_nuke import constants as nuke_constants


class BaseNukePlugin(plugin.BasePlugin):
    host = nuke_constants.HOST

    def _run(self, event):
        super_fn = super(BaseNukePlugin, self)._run
        result = super_fn(event)
        #result = nuke.executeInMainThreadWithResult(super_fn, event)
        return result


class BaseNukePluginWidget(BaseNukePlugin, pluginWidget.BasePluginWidget):
    type = 'widget'
    ui = nuke_constants.UI

from ftrack_connect_pipeline_nuke.plugin.load import *
from ftrack_connect_pipeline_nuke.plugin.publish import *
