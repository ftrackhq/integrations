# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import maya

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_maya.plugin import (
    BaseMayaPlugin,
    BaseMayaPluginWidget,
)

from ftrack_connect_pipeline_maya.utils import custom_commands as maya_utils
from ftrack_connect_pipeline_maya.asset import FtrackAssetNode
from ftrack_connect_pipeline_maya.constants.asset import modes as load_const
from ftrack_connect_pipeline_maya.constants import asset as asset_const


class LoaderImporterMayaPlugin(plugin.LoaderImporterPlugin, BaseMayaPlugin):
    '''Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''

    ftrack_asset_class = FtrackAssetNode

    load_modes = load_const.LOAD_MODES

    dependency_load_mode = load_const.REFERENCE_MODE

    @maya_utils.run_in_main_thread
    def get_current_objects(self):
        return maya_utils.get_current_scene_objects()


class LoaderImporterMayaWidget(
    pluginWidget.LoaderImporterWidget, BaseMayaPluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''

    @maya_utils.run_in_main_thread
    def _run(self, event):
        return super(LoaderImporterMayaWidget, self)._run, event
