# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_core import plugin
from ftrack_framework_qt import plugin as pluginWidget
from ftrack_framework_3dsmax.plugin import (
    MaxBasePlugin,
    MaxBasePluginWidget,
)

from ftrack_framework_3dsmax import utils as max_utils
from ftrack_framework_3dsmax.constants.asset import modes as load_const


class MaxOpenerImporterPlugin(plugin.OpenerImporterPlugin, MaxBasePlugin):
    '''Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''

    load_modes = {
        load_const.OPEN_MODE: load_const.LOAD_MODES[load_const.OPEN_MODE]
    }

    dependency_load_mode = load_const.OPEN_MODE

    @max_utils.run_in_main_thread
    def get_current_objects(self):
        return max_utils.get_current_scene_objects()


class MaxOpenerImporterPluginWidget(
    pluginWidget.OpenerImporterPluginWidget, MaxBasePluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
