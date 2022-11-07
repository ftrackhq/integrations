# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_3dsmax.plugin import (
    MaxBasePlugin,
    MaxBasePluginWidget,
)

from ftrack_connect_pipeline_3dsmax.utils import custom_commands as max_utils
from ftrack_connect_pipeline_3dsmax.constants.asset import modes as load_const
from ftrack_connect_pipeline_3dsmax.constants import asset as asset_const


class MaxLoaderImporterPlugin(plugin.LoaderImporterPlugin, MaxBasePlugin):
    '''Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''

    load_modes = load_const.LOAD_MODES

    dependency_load_mode = load_const.REFERENCE_MODE

    @max_utils.run_in_main_thread
    def get_current_objects(self):
        return max_utils.get_current_scene_objects()


class MaxLoaderImporterPluginWidget(
    pluginWidget.LoaderImporterPluginWidget, MaxBasePluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
