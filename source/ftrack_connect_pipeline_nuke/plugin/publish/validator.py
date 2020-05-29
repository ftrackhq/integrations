# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_nuke.plugin import (
    BaseNukePlugin, BaseNukePluginWidget
)


class PublisherValidatorNukePlugin(
    plugin.PublisherValidatorPlugin, BaseNukePlugin
):
    ''' Class representing a Validator Plugin

    .. note::

        _required_output a Boolean
    '''


class PublisherValidatorNukeWidget(
    pluginWidget.PublisherValidatorWidget, BaseNukePluginWidget
):
    ''' Class representing a Validator widget

    .. note::

        _required_output a Boolean
    '''
