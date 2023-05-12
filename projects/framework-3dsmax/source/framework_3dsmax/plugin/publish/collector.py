# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from framework_core import plugin
from framework_qt import plugin as pluginWidget
from framework_3dsmax.plugin import (
    MaxBasePlugin,
    MaxBasePluginWidget,
)


class MaxPublisherCollectorPlugin(
    plugin.PublisherCollectorPlugin, MaxBasePlugin
):
    '''Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''


class MaxPublisherCollectorPluginWidget(
    pluginWidget.PublisherCollectorPluginWidget, MaxBasePluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
