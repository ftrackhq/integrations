# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_nuke.plugin import (
    NukeBasePlugin,
    NukeBasePluginWidget,
)


class NukeOpenerPostImporterPlugin(
    plugin.OpenerPostImporterPlugin, NukeBasePlugin
):
    '''Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''


class NukeOpenerPostImporterPluginWidget(
    pluginWidget.OpenerPostImporterPluginWidget, NukeBasePluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
