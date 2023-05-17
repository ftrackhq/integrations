# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from framework_core import plugin
from framework_qt import plugin as pluginWidget
from framework_3dsmax.plugin import (
    MaxBasePlugin,
    MaxBasePluginWidget,
)

from framework_3dsmax import utils as max_utils
from framework_3dsmax.constants.asset import modes as load_const


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
