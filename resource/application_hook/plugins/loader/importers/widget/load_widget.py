# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_qt.client.widgets.options.load_widget import (
    LoadBaseWidget
)
from ftrack_connect_pipeline_nuke.constants.asset import modes as load_const


class LoadNukeWidget(LoadBaseWidget):
    load_modes = load_const.LOAD_MODES.keys()


class LoadNukePluginWidget(plugin.LoaderImporterNukeWidget):
    plugin_name = 'load_nuke'
    widget = LoadNukeWidget


def register(api_object, **kw):
    plugin = LoadNukePluginWidget(api_object)
    plugin.register()
