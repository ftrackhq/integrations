# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_maya.plugin import (
    MayaBasePlugin,
    MayaBasePluginWidget,
)


class MayaPublisherExporterPlugin(
    plugin.PublisherExporterPlugin, MayaBasePlugin
):
    '''Class representing an Exporter Plugin
    .. note::

        _required_output a Dictionary
    '''


class MayaPublisherExporterPluginWidget(
    pluginWidget.PublisherExporterPluginWidget, MayaBasePluginWidget
):
    '''Class representing an Eporter Widget
    .. note::

        _required_output a Dictionary
    '''
