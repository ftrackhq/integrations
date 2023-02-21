# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_connect_pipeline import plugin

from ftrack_connect_pipeline_qt import plugin as pluginWidget

from ftrack_connect_pipeline_unreal.plugin import (
    UnrealBasePlugin,
    UnrealBasePluginWidget,
)


class UnrealPublisherCollectorPlugin(
    plugin.PublisherCollectorPlugin, UnrealBasePlugin
):
    '''Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''


class UnrealPublisherCollectorPluginWidget(
    pluginWidget.PublisherCollectorPluginWidget, UnrealBasePluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
