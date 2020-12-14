# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_houdini import constants as houdini_constants

import hdefereval


class BaseHoudiniPlugin(plugin.BasePlugin):
    host_type = houdini_constants.HOST_TYPE
    ''' '''
    # def _run(self, event):
    #     super_fn = super(BaseHoudiniPlugin, self)._run
    #
    #     result = hdefereval.executeInMainThreadWithResult(super_fn)
    #
    #     return result


class BaseHoudiniPluginWidget(BaseHoudiniPlugin, pluginWidget.BasePluginWidget):
    type = 'widget'
    ui_type = houdini_constants.UI_TYPE

    #def _run(self, event):
    #    super_fn = super(BaseHoudiniPluginWidget, self)._run
    #
    #    result = hdefereval.executeInMainThreadWithResult(super_fn)
    #
    #   return result


from ftrack_connect_pipeline_houdini.plugin.load import *
from ftrack_connect_pipeline_houdini.plugin.publish import *
from ftrack_connect_pipeline_houdini.plugin.asset_manager import *
