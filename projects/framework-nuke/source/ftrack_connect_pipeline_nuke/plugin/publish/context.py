# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_nuke.plugin import (
    NukeBasePlugin,
    NukeBasePluginWidget,
)


class NukePublisherContextPlugin(
    plugin.PublisherContextPlugin, NukeBasePlugin
):
    '''Class representing a Context Plugin
    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'comment' and 'status_id' of the current asset
    '''


class NukePublisherContextPluginWidget(
    pluginWidget.PublisherContextPluginWidget, NukeBasePluginWidget
):
    '''Class representing a Context Widget
    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'comment' and 'status_id' of the current asset
    '''
