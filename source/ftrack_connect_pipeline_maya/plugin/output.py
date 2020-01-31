# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_maya.plugin import (
    BaseMayaPlugin, BaseMayaPluginWidget
)


class OutputMayaPlugin(plugin.OutputPlugin, BaseMayaPlugin):
    ''' Class representing an Output Plugin
    .. note::

        _required_output a Dictionary '''


class OutputMayaWidget(pluginWidget.OutputWidget, BaseMayaPluginWidget):
    ''' Class representing an Output Widget
        .. note::

            _required_output a Dictionary '''
