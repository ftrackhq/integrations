# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_harmony.plugin import (
    HarmonyBasePlugin,
    HarmonyBasePluginWidget,
)

from ftrack_connect_pipeline_harmony import utils as harmony_utils
from ftrack_connect_pipeline_harmony.constants.asset import modes as load_const
from ftrack_connect_pipeline_harmony.constants import asset as asset_const


class HarmonyLoaderImporterPlugin(plugin.LoaderImporterPlugin, HarmonyBasePlugin):
    '''Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''

    load_modes = load_const.LOAD_MODES

    dependency_load_mode = load_const.REFERENCE_MODE

    @harmony_utils.run_in_main_thread
    def get_current_objects(self):
        return harmony_utils.get_current_scene_objects()


class HarmonyLoaderImporterPluginWidget(
    pluginWidget.LoaderImporterPluginWidget, HarmonyBasePluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
