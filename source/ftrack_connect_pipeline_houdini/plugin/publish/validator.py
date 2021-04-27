# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_houdini.plugin import (
    BaseHoudiniPlugin, BaseHoudiniPluginWidget
)


class PublisherValidatorHoudiniPlugin(
    plugin.PublisherValidatorPlugin, BaseHoudiniPlugin
):
    ''' Class representing a Validator Plugin

    .. note::

        _required_output a Boolean
    '''


class PublisherValidatorHoudiniWidget(
    pluginWidget.PublisherValidatorWidget, BaseHoudiniPluginWidget
):
    ''' Class representing a Validator widget

    .. note::

        _required_output a Boolean
    '''
