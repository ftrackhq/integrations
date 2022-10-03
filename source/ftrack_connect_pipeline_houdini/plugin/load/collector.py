# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_houdini.plugin import (
    HoudiniBasePlugin,
    HoudiniBasePluginWidget,
)


class HoudiniLoaderCollectorHoudiniPlugin(
    plugin.LoaderCollectorPlugin, HoudiniBasePlugin
):
    '''Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''


class HoudiniLoaderCollectorHoudiniWidget(
    pluginWidget.LoaderCollectorPluginWidget, HoudiniBasePluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
