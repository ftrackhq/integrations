# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from framework_core import plugin
from framework_qt import plugin as pluginWidget
from framework_houdini.plugin import (
    HoudiniBasePlugin,
    HoudiniBasePluginWidget,
)

from framework_houdini.constants.asset import modes as load_const
from framework_houdini import utils as houdini_utils


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
