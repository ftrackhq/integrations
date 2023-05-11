# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_houdini.plugin import (
    HoudiniBasePlugin,
    HoudiniBasePluginWidget,
)

from ftrack_connect_pipeline_houdini import utils as houdini_utils
from ftrack_connect_pipeline_houdini.constants.asset import modes as load_const


class HoudiniOpenerImporterPlugin(
    plugin.OpenerImporterPlugin, HoudiniBasePlugin
):
    '''Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''

    load_modes = {
        load_const.OPEN_MODE: load_const.LOAD_MODES[load_const.OPEN_MODE]
    }

    dependency_load_mode = load_const.OPEN_MODE

    @houdini_utils.run_in_main_thread
    def get_current_objects(self):
        return houdini_utils.get_current_scene_objects()


class HoudiniOpenerImporterPluginWidget(
    pluginWidget.OpenerImporterPluginWidget, HoudiniBasePluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
