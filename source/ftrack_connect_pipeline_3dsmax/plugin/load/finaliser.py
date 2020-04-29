# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_3dsmax.plugin import (
    BaseMaxPlugin, BaseMaxPluginWidget
)


class LoaderFinaliserMaxPlugin(plugin.LoaderFinaliserPlugin, BaseMaxPlugin):
    ''' Class representing a Finaliser Plugin

        .. note::

            _required_output is a dictionary containing the 'context_id',
            'asset_name', 'asset_type', 'comment' and 'status_id' of the
            current asset
    '''


class LoaderFinaliserMaxWidget(
    pluginWidget.LoaderFinaliserWidget, BaseMaxPluginWidget
):
    ''' Class representing a Finaliser Widget

        .. note::

            _required_output is a dictionary containing the 'context_id',
            'asset_name', 'asset_type', 'comment' and 'status_id' of the
            current asset
    '''
