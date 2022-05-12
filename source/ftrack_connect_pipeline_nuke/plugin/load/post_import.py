# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_nuke.plugin import (
    NukeBasePlugin,
    NukeBasePluginWidget,
)


class NukeLoaderPostImportPlugin(
    plugin.LoaderPostImportPlugin, NukeBasePlugin
):
    '''Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''


class NukeLoaderPostImportPluginWidget(
    pluginWidget.LoaderPostImportPluginWidget, NukeBasePluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
