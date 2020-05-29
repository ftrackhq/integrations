# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_nuke.plugin import (
    BaseNukePlugin, BaseNukePluginWidget
)


class PublisherOutputNukePlugin(plugin.PublisherOutputPlugin, BaseNukePlugin):
    ''' Class representing an Output Plugin
    .. note::

        _required_output a Dictionary
    '''


class PublisherOutputNukeWidget(
    pluginWidget.PublisherOutputWidget, BaseNukePluginWidget
):
    ''' Class representing an Output Widget
        .. note::

            _required_output a Dictionary
    '''
