# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_framework_core import plugin
from ftrack_framework_qt import plugin as pluginWidget
from ftrack_framework_3dsmax.plugin import (
    MaxBasePlugin,
    MaxBasePluginWidget,
)


class MaxPublisherExporterPlugin(
    plugin.PublisherExporterPlugin, MaxBasePlugin
):
    '''Class representing an Exporter Plugin
    .. note::

        _required_output a Dictionary
    '''


class MaxPublisherExporterPluginWidget(
    pluginWidget.PublisherExporterPluginWidget, MaxBasePluginWidget
):
    '''Class representing an Eporter Widget
    .. note::

        _required_output a Dictionary
    '''
