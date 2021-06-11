# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_3dsmax.plugin import (
    BaseMaxPlugin, BaseMaxPluginWidget
)


class LoaderPreFinalizerMaxPlugin(plugin.LoaderPreFinalizerPlugin, BaseMaxPlugin):
    ''' Class representing a Pre Finalizer Plugin

        .. note::

            _required_output is a dictionary containing the 'context_id',
            'asset_name', 'asset_type_name', 'comment' and 'status_id' of the
            current asset
    '''


class LoaderPreFinalizerMaxWidget(
    pluginWidget.LoaderPreFinalizerWidget, BaseMaxPluginWidget
):
    ''' Class representing a Pre Finalizer Widget

        .. note::

            _required_output is a dictionary containing the 'context_id',
            'asset_name', 'asset_type_name', 'comment' and 'status_id' of the
            current asset
    '''
