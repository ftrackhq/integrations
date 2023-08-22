# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_core import plugin
from ftrack_framework_qt import plugin as pluginWidget
from ftrack_framework_houdini.plugin import (
    HoudiniBasePlugin,
    HoudiniBasePluginWidget,
)


class HoudiniPublisherExporterPlugin(
    plugin.PublisherExporterPlugin, HoudiniBasePlugin
):
    '''Class representing an Output Plugin
    .. note::

        _required_output a Dictionary
    '''


class HoudiniPublisherExporterPluginWidget(
    pluginWidget.PublisherExporterPluginWidget, HoudiniBasePluginWidget
):
    '''Class representing an Output Widget
    .. note::

        _required_output a Dictionary
    '''
