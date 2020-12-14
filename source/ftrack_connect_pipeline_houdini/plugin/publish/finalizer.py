# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack
import os
import re
import clique

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_houdini.plugin import (
    BaseHoudiniPlugin, BaseHoudiniPluginWidget
)
from ftrack_connect_pipeline_houdini.constants import asset as asset_const
from ftrack_connect_pipeline_houdini.utils import custom_commands as houdini_utils


class PublisherFinalizerHoudiniPlugin(plugin.PublisherFinalizerPlugin, BaseHoudiniPlugin):
    ''' Class representing a Finalizer Plugin

        .. note::

            _required_output is a dictionary containing the 'context_id',
            'asset_name', 'asset_type', 'comment' and 'status_id' of the
            current asset
    '''


class PublisherFinalizerHoudiniWidget(
    pluginWidget.PublisherFinalizerWidget, BaseHoudiniPluginWidget
):
    ''' Class representing a Finalizer Widget

        .. note::

            _required_output is a dictionary containing the 'context_id',
            'asset_name', 'asset_type', 'comment' and 'status_id' of the
            current asset
    '''
