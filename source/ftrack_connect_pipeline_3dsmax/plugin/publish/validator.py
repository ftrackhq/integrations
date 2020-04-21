# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_3dsmax.plugin import (
    BaseMaxPlugin, BaseMaxPluginWidget
)


class PublisherValidatorMaxPlugin(
    plugin.PublisherValidatorPlugin, BaseMaxPlugin
):
    ''' Class representing a Validator Plugin

    .. note::

        _required_output a Boolean
    '''


class PublisherValidatorMaxWidget(
    pluginWidget.PublisherValidatorWidget, BaseMaxPluginWidget
):
    ''' Class representing a Validator widget

    .. note::

        _required_output a Boolean
    '''
