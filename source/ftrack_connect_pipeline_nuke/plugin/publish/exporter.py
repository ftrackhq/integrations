# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_nuke.plugin import (
    NukeBasePlugin,
    NukeBasePluginWidget,
)


class NukePublisherExporterPlugin(
    plugin.PublisherExporterPlugin, NukeBasePlugin
):
    '''Class representing an exporter Plugin
    .. note::

        _required_output a Dictionary
    '''


class NukePublisherExporterPluginWidget(
    pluginWidget.PublisherExporterPluginWidget, NukeBasePluginWidget
):
    '''Class representing an exporter Widget
    .. note::

        _required_output a Dictionary
    '''
