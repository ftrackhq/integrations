# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_connect_pipeline import plugin

from ftrack_connect_pipeline_qt import plugin as pluginWidget

from ftrack_connect_pipeline_unreal.plugin import (
    UnrealBasePlugin,
    UnrealBasePluginWidget,
)


class UnrealPublisherContextPlugin(
    plugin.PublisherContextPlugin, UnrealBasePlugin
):
    '''Class representing a Context Plugin
    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'comment' and 'status_id' of the current asset
    '''


class UnrealPublisherContextPluginWidget(
    pluginWidget.PublisherContextPluginWidget, UnrealBasePluginWidget
):
    '''Class representing a Context Widget
    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'comment' and 'status_id' of the current asset
    '''
