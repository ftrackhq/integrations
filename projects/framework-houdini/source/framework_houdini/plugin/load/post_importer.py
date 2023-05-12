# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from framework_core import plugin
from framework_qt import plugin as pluginWidget
from framework_houdini.plugin import (
    HoudiniBasePlugin,
    HoudiniBasePluginWidget,
)


class HoudiniLoaderPostImporterPlugin(
    plugin.LoaderPostImporterPlugin, HoudiniBasePlugin
):
    '''Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''


class HoudiniLoaderPostImporterPluginWidget(
    pluginWidget.LoaderPostImporterPluginWidget, HoudiniBasePluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
