# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_maya.plugin import (
    BaseMayaPlugin,
    BaseMayaPluginWidget,
)


class MayaPublisherExporterPlugin(plugin.PublisherExporterPlugin, BaseMayaPlugin):
    '''Class representing an Exporter Plugin
    .. note::

        _required_output a Dictionary
    '''


class MayaPublisherExporterPluginWidget(
    pluginWidget.PublisherExporterPluginWidget, BaseMayaPluginWidget
):
    '''Class representing an Eporter Widget
    .. note::

        _required_output a Dictionary
    '''
