# :coding: utf-8
# :copyright: Copyright (c) 2020 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_houdini.plugin import (
    BaseHoudiniPlugin, BaseHoudiniPluginWidget
)


class LoaderPostImportHoudiniPlugin(plugin.LoaderPostImportPlugin, BaseHoudiniPlugin):
    ''' Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''


class LoaderPostImportHoudiniWidget(
    pluginWidget.LoaderPostImportWidget, BaseHoudiniPluginWidget
):
    ''' Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
