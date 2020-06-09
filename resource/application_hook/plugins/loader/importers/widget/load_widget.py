# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline_3dsmax import plugin
from ftrack_connect_pipeline_qt.client.widgets.options.load_widget import (
    LoadBaseWidget
)
from ftrack_connect_pipeline_3dsmax.constants import asset as asset_const


class Load3dsMaxWidget(LoadBaseWidget):
    load_modes = asset_const.LOAD_MODES.keys()

class Load3dsMaxPluginWidget(plugin.LoaderImporterMaxWidget):
    plugin_name = 'load_max'
    widget = Load3dsMaxWidget


def register(api_object, **kw):
    plugin = Load3dsMaxPluginWidget(api_object)
    plugin.register()
