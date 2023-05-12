# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from framework_core import plugin
from framework_qt import plugin as pluginWidget
from framework_3dsmax.plugin import (
    MaxBasePlugin,
    MaxBasePluginWidget,
)


class MaxOpenerCollectorPlugin(plugin.OpenerCollectorPlugin, MaxBasePlugin):
    '''Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''


class MaxOpenerCollectorPluginWidget(
    pluginWidget.OpenerCollectorPluginWidget, MaxBasePluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
