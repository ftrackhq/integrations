# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import threading

import nuke

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_nuke.plugin import (
    NukeBasePlugin,
    NukeBasePluginWidget,
)

from ftrack_connect_pipeline_nuke.constants import asset as asset_const
from ftrack_connect_pipeline_nuke.constants.asset import modes as load_const
from ftrack_connect_pipeline_nuke import utils as nuke_utils


class NukeLoaderImporterPlugin(plugin.LoaderImporterPlugin, NukeBasePlugin):
    '''Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''

    load_modes = load_const.LOAD_MODES

    dependency_load_mode = load_const.IMPORT_MODE

    @nuke_utils.run_in_main_thread
    def get_current_objects(self):
        return nuke_utils.get_current_scene_objects()


class NukeLoaderImporterPluginWidget(
    pluginWidget.LoaderImporterPluginWidget, NukeBasePluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
