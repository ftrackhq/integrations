# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_houdini.plugin import (
    HoudiniBasePlugin,
    HoudiniBasePluginWidget,
)

from ftrack_connect_pipeline_houdini.constants.asset import modes as load_const
from ftrack_connect_pipeline_houdini import utils as houdini_utils


class HoudiniLoaderImporterPlugin(
    plugin.LoaderImporterPlugin, HoudiniBasePlugin
):
    '''Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''

    load_modes = load_const.LOAD_MODES

    dependency_load_mode = load_const.IMPORT_MODE

    @houdini_utils.run_in_main_thread
    def get_current_objects(self):
        return houdini_utils.get_current_scene_objects()


class HoudiniLoaderImporterPluginWidget(
    pluginWidget.LoaderImporterPluginWidget, HoudiniBasePluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
