# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import maya

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_maya.plugin import (
    MayaBasePlugin,
    MayaBasePluginWidget,
)

from ftrack_connect_pipeline_maya import utils as maya_utils
from ftrack_connect_pipeline_maya.constants.asset import modes as load_const


class MayaLoaderImporterPlugin(plugin.LoaderImporterPlugin, MayaBasePlugin):
    '''Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''

    load_modes = load_const.LOAD_MODES

    dependency_load_mode = load_const.REFERENCE_MODE

    @maya_utils.run_in_main_thread
    def get_current_objects(self):
        return maya_utils.get_current_scene_objects()


class MayaLoaderImporterPluginWidget(
    pluginWidget.LoaderImporterPluginWidget, MayaBasePluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
