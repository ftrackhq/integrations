# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import ftrack_api

from ftrack_connect_pipeline_3dsmax import plugin
from ftrack_connect_pipeline_qt.client.widgets.options.load_widget import (
    LoadBaseWidget
)
from ftrack_connect_pipeline_3dsmax.constants.asset import modes as load_const


class Load3dsMaxWidget(LoadBaseWidget):
    load_modes = load_const.LOAD_MODES.keys()

class Load3dsMaxPluginWidget(plugin.LoaderImporterMaxWidget):
    plugin_name = 'load_max'
    widget = Load3dsMaxWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = Load3dsMaxPluginWidget(api_object)
    plugin.register()
