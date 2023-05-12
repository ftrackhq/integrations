# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from framework_core import plugin

from framework_qt import plugin as pluginWidget

from framework_unreal.plugin import (
    UnrealBasePlugin,
    UnrealBasePluginWidget,
)


class UnrealPublisherPostFinalizerPlugin(
    plugin.PublisherPostFinalizerPlugin, UnrealBasePlugin
):
    '''Class representing a Post Finalizer Plugin

    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'asset_type_name', 'comment' and 'status_id' of the
        current asset
    '''


class UnrealPublisherPostFinalizerPluginWidget(
    pluginWidget.PublisherPostFinalizerPluginWidget, UnrealBasePluginWidget
):
    '''Class representing a Finalizer Widget

    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'asset_type_name', 'comment' and 'status_id' of the
        current asset
    '''
