# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import ftrack_api

from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_qt.plugin.widget.load_widget import (
    LoadBaseWidget,
)
from ftrack_connect_pipeline_nuke.constants.asset import modes as load_const


class NukeNativeLoaderImporterOptionsWidget(LoadBaseWidget):
    '''Nuke loader import options user input test/template plugin widget'''

    load_modes = list(load_const.LOAD_MODES.keys())


class NukeNativeLoaderImporterPluginWidget(
    plugin.NukeLoaderImporterPluginWidget
):
    plugin_name = 'nuke_native_loader_importer'
    widget = NukeNativeLoaderImporterOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeNativeLoaderImporterPluginWidget(api_object)
    plugin.register()
