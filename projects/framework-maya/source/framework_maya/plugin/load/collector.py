# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from framework_core import plugin
from framework_qt import plugin as pluginWidget
from framework_maya.plugin import (
    MayaBasePlugin,
    MayaBasePluginWidget,
)


class MayaLoaderCollectorPlugin(plugin.LoaderCollectorPlugin, MayaBasePlugin):
    '''Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''


class MayaLoaderCollectorPluginWidget(
    pluginWidget.LoaderCollectorPluginWidget, MayaBasePluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
