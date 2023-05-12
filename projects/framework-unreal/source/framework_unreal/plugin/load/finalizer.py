# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from framework_core import plugin

from framework_qt import plugin as pluginWidget

from framework_unreal.plugin import (
    UnrealBasePlugin,
    UnrealBasePluginWidget,
)


class UnrealLoaderFinalizerPlugin(
    plugin.LoaderFinalizerPlugin, UnrealBasePlugin
):
    '''Class representing a Finalizer Plugin

    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'asset_type_name', 'comment' and 'status_id' of the
        current asset
    '''


class UnrealLoaderFinalizerPluginWidget(
    pluginWidget.LoaderFinalizerPluginWidget, UnrealBasePluginWidget
):
    '''Class representing a Finalizer Widget

    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'asset_type_name', 'comment' and 'status_id' of the
        current asset
    '''
