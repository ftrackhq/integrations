# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_harmony.plugin import (
    HarmonyBasePlugin,
    HarmonyBasePluginWidget,
)


class HarmonyPublisherExporterPlugin(
    plugin.PublisherExporterPlugin, HarmonyBasePlugin
):
    '''Class representing an Exporter Plugin
    .. note::

        _required_output a Dictionary
    '''


class HarmonyPublisherExporterPluginWidget(
    pluginWidget.PublisherExporterPluginWidget, HarmonyBasePluginWidget
):
    '''Class representing an Eporter Widget
    .. note::

        _required_output a Dictionary
    '''
