# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from framework_core import plugin
from framework_qt import plugin as pluginWidget
from framework_nuke.plugin import (
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
