# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_houdini.plugin import (
    BaseHoudiniPlugin, BaseHoudiniPluginWidget
)


class PublisherOutputHoudiniPlugin(plugin.PublisherOutputPlugin,
                                   BaseHoudiniPlugin):
    ''' Class representing an Output Plugin
    .. note::

        _required_output a Dictionary
    '''


class PublisherOutputHoudiniWidget(
    pluginWidget.PublisherOutputWidget, BaseHoudiniPluginWidget
):
    ''' Class representing an Output Widget
        .. note::

            _required_output a Dictionary
    '''
