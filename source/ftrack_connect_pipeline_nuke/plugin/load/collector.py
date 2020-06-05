# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_nuke.plugin import (
    BaseNukePlugin, BaseNukePluginWidget
)


class LoaderCollectorNukePlugin(plugin.LoaderCollectorPlugin, BaseNukePlugin):
    ''' Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''


class LoaderCollectorNukeWidget(
    pluginWidget.LoaderCollectorWidget, BaseNukePluginWidget
):
    ''' Class representing a Collector Widget

    .. note::

        _required_output a List
    '''

