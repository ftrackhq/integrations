# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import threading

import nuke

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_nuke.plugin import (
    BaseNukePlugin,
    BaseNukePluginWidget,
)

from ftrack_connect_pipeline_nuke.asset import FtrackAssetTab
from ftrack_connect_pipeline_nuke.constants import asset as asset_const
from ftrack_connect_pipeline_nuke.constants.asset import modes as load_const
from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils


class OpenerImporterNukePlugin(plugin.OpenerImporterPlugin, BaseNukePlugin):
    '''Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''

    ftrack_asset_class = FtrackAssetTab

    load_modes = load_const.LOAD_MODES

    dependency_load_mode = load_const.REFERENCE_MODE

    @nuke_utils.run_in_main_thread
    def get_current_objects(self):
        return nuke_utils.get_current_scene_objects()


class OpenerImporterNukeWidget(
    pluginWidget.OpenerImporterWidget, BaseNukePluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
