# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_houdini.plugin import (
    BaseHoudiniPlugin, BaseHoudiniPluginWidget
)


class LoaderPostFinalizerHoudiniPlugin(plugin.LoaderPostFinalizerPlugin,
                                       BaseHoudiniPlugin):
    ''' Class representing a Post Finalizer Plugin

        .. note::

            _required_output is a dictionary containing the 'context_id',
            'asset_name', 'asset_type', 'comment' and 'status_id' of the
            current asset
    '''


class LoaderPostFinalizerHoudiniWidget(
    pluginWidget.LoaderPostFinalizerWidget, BaseHoudiniPluginWidget
):
    ''' Class representing a Post Finalizer Widget

        .. note::

            _required_output is a dictionary containing the 'context_id',
            'asset_name', 'asset_type', 'comment' and 'status_id' of the
            current asset
    '''