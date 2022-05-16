# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

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
from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils


class NukeOpenerImporterPlugin(plugin.OpenerImporterPlugin, NukeBasePlugin):
    '''Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''

    load_modes = {
        load_const.OPEN_MODE: load_const.LOAD_MODES[load_const.OPEN_MODE]
    }

    dependency_load_mode = load_const.OPEN_MODE

    @nuke_utils.run_in_main_thread
    def get_current_objects(self):
        return nuke_utils.get_current_scene_objects()


class NukeOpenerImporterPluginWidget(
    pluginWidget.OpenerImporterPluginWidget, NukeBasePluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
