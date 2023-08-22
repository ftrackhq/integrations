# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_core import plugin
from ftrack_framework_qt import plugin as pluginWidget
from ftrack_framework_houdini.plugin import (
    HoudiniBasePlugin,
    HoudiniBasePluginWidget,
)


class HoudiniLoaderPreFinalizerPlugin(
    plugin.LoaderPreFinalizerPlugin, HoudiniBasePlugin
):
    '''Class representing a Pre Finalizer Plugin

    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'asset_type_name', 'comment' and 'status_id' of the
        current asset
    '''


class HoudiniLoaderPreFinalizerPluginWidget(
    pluginWidget.LoaderPreFinalizerPluginWidget, HoudiniBasePluginWidget
):

    '''Class representing a Pre Finalizer Widget

    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'asset_type_name', 'comment' and 'status_id' of the
        current asset
    '''
