# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_nuke.plugin import (
    NukeBasePlugin,
    NukeBasePluginWidget,
)


class NukeOpenerPreFinalizerPlugin(
    plugin.OpenerPreFinalizerPlugin, NukeBasePlugin
):
    '''Class representing a Pre Finalizer Plugin

    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'asset_type_name', 'comment' and 'status_id' of the
        current asset
    '''


class NukeOpenerPreFinalizerPluginWidget(
    pluginWidget.OpenerPreFinalizerPluginWidget, NukeBasePluginWidget
):
    '''Class representing a Pre Finalizer Widget

    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'asset_type_name', 'comment' and 'status_id' of the
        current asset
    '''
