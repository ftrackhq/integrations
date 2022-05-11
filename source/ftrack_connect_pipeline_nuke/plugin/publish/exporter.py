# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_nuke.plugin import (
    BaseNukePlugin,
    BaseNukePluginWidget,
)


class NukePublisherExporterPlugin(plugin.PublisherExporterPlugin, BaseNukePlugin):
    '''Class representing an exporter Plugin
    .. note::

        _required_output a Dictionary
    '''


class NukePublisherExporterPluginWidget(
    pluginWidget.PublisherExporterPluginWidget, BaseNukePluginWidget
):
    '''Class representing an exporter Widget
    .. note::

        _required_output a Dictionary
    '''
