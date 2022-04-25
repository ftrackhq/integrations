# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_nuke.plugin import (
    BaseNukePlugin,
    BaseNukePluginWidget,
)


class OpenerCollectorNukePlugin(plugin.OpenerCollectorPlugin, BaseNukePlugin):
    '''Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''


class OpenerCollectorNukeWidget(
    pluginWidget.OpenerCollectorWidget, BaseNukePluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
