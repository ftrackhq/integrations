# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_harmony.plugin import (
    HarmonyBasePlugin,
    HarmonyBasePluginWidget,
)


class HarmonyLoaderCollectorPlugin(plugin.LoaderCollectorPlugin, HarmonyBasePlugin):
    '''Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''


class HarmonyLoaderCollectorPluginWidget(
    pluginWidget.LoaderCollectorPluginWidget, HarmonyBasePluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
