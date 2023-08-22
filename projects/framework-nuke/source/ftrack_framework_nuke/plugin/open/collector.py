# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_core import plugin
from ftrack_framework_qt import plugin as pluginWidget
from ftrack_framework_nuke.plugin import (
    NukeBasePlugin,
    NukeBasePluginWidget,
)


class NukeOpenerCollectorPlugin(plugin.OpenerCollectorPlugin, NukeBasePlugin):
    '''Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''


class NukeOpenerCollectorPluginWidget(
    pluginWidget.OpenerCollectorPluginWidget, NukeBasePluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
