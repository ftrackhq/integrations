# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_maya.plugin import (
    BaseMayaPlugin, BaseMayaPluginWidget
)


class PublisherCollectorMayaPlugin(
    plugin.PublisherCollectorPlugin, BaseMayaPlugin
):
    ''' Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''


class PublisherCollectorMayaWidget(
    pluginWidget.PublisherCollectorWidget, BaseMayaPluginWidget
):
    ''' Class representing a Collector Widget

    .. note::

        _required_output a List
    '''

