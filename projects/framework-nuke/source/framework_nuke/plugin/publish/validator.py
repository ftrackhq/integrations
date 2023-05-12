# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from framework_core import plugin
from framework_qt import plugin as pluginWidget
from framework_nuke.plugin import (
    NukeBasePlugin,
    NukeBasePluginWidget,
)


class NukePublisherValidatorPlugin(
    plugin.PublisherValidatorPlugin, NukeBasePlugin
):
    '''Class representing a Validator Plugin

    .. note::

        _required_output a Boolean
    '''


class NukePublisherValidatorPluginWidget(
    pluginWidget.PublisherValidatorPluginWidget, NukeBasePluginWidget
):
    '''Class representing a Validator widget

    .. note::

        _required_output a Boolean
    '''
