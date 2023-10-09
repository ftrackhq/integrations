# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_core import plugin

from ftrack_framework_qt import plugin as pluginWidget

from ftrack_framework_unreal.plugin import (
    UnrealBasePlugin,
    UnrealBasePluginWidget,
)


class UnrealLoaderCollectorPlugin(
    plugin.LoaderCollectorPlugin, UnrealBasePlugin
):
    '''Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''


class UnrealLoaderCollectorPluginWidget(
    pluginWidget.LoaderCollectorPluginWidget, UnrealBasePluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
