# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_qt.client.widgets.options.load_widget import (
    LoadBaseWidget
)
from ftrack_connect_pipeline_nuke.constants import asset as asset_const


class LoadNukeWidget(LoadBaseWidget):
    load_modes = [
        asset_const.OPEN_MODE,
        asset_const.IMPORT_MODE,
        asset_const.REFERENCE_MODE
    ]


class LoadNukePluginWidget(plugin.LoaderImporterNukeWidget):
    plugin_name = 'load_nuke'
    widget = LoadNukeWidget


def register(api_object, **kw):
    plugin = LoadNukePluginWidget(api_object)
    plugin.register()
