# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_houdini.plugin import (
    BaseHoudiniPlugin, BaseHoudiniPluginWidget
)


class LoaderPreFinalizerHoudiniPlugin(plugin.LoaderPreFinalizerPlugin,
                                      BaseHoudiniPlugin):
    ''' Class representing a Pre Finalizer Plugin

        .. note::

            _required_output is a dictionary containing the 'context_id',
            'asset_name', 'asset_type', 'comment' and 'status_id' of the
            current asset
    '''


class LoaderPreFinalizerHoudiniWidget(
    pluginWidget.LoaderPreFinalizerWidget, BaseHoudiniPluginWidget
):

    ''' Class representing a Pre Finalizer Widget

        .. note::

            _required_output is a dictionary containing the 'context_id',
            'asset_name', 'asset_type', 'comment' and 'status_id' of the
            current asset
    '''