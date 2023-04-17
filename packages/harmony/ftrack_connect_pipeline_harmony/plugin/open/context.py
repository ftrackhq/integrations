# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_harmony.plugin import (
    HarmonyBasePlugin,
    HarmonyBasePluginWidget,
)


class HarmonyOpenerContextPlugin(
    plugin.OpenerContextPlugin, HarmonyBasePlugin
):
    '''Class representing a Context Plugin
    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'comment' and 'status_id' of the current asset
    '''


class HarmonyOpenerContextPluginWidget(
    pluginWidget.OpenerContextPluginWidget, HarmonyBasePluginWidget
):
    '''Class representing a Context Widget
    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'comment' and 'status_id' of the current asset
    '''
