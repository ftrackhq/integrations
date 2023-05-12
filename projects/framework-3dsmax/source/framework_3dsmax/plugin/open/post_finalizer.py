# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from framework_core import plugin
from framework_qt import plugin as pluginWidget
from framework_3dsmax.plugin import (
    MaxBasePlugin,
    MaxBasePluginWidget,
)


class MaxOpenerPostFinalizerPlugin(
    plugin.OpenerPostFinalizerPlugin, MaxBasePlugin
):
    '''Class representing a Post Finalizer Plugin

    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'asset_type_name', 'comment' and 'status_id' of the
        current asset
    '''


class MaxOpenerPostFinalizerPluginWidget(
    pluginWidget.OpenerPostFinalizerPluginWidget, MaxBasePluginWidget
):
    '''Class representing a Post Finalizer Widget

    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'asset_type_name', 'comment' and 'status_id' of the
        current asset
    '''
