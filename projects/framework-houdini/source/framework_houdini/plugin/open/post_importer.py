# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from framework_core import plugin
from framework_qt import plugin as pluginWidget
from framework_houdini.plugin import (
    HoudiniBasePlugin,
    HoudiniBasePluginWidget,
)


class HoudiniOpenerPostImporterPlugin(
    plugin.OpenerPostImporterPlugin, HoudiniBasePlugin
):
    '''Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''


class HoudiniOpenerPostImporterPluginWidget(
    pluginWidget.OpenerPostImporterPluginWidget, HoudiniBasePluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
