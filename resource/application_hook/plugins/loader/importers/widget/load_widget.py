# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import ftrack_api

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
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = LoadNukePluginWidget(api_object)
    plugin.register()
