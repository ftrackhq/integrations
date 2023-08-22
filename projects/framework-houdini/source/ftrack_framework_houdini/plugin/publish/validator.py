# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_core import plugin
from ftrack_framework_qt import plugin as pluginWidget
from ftrack_framework_houdini.plugin import (
    HoudiniBasePlugin,
    HoudiniBasePluginWidget,
)


class HoudiniPublisherValidatorPlugin(
    plugin.PublisherValidatorPlugin, HoudiniBasePlugin
):
    '''Class representing a Validator Plugin

    .. note::

        _required_output a Boolean
    '''


class HoudiniPublisherValidatorPluginWidget(
    pluginWidget.PublisherValidatorPluginWidget, HoudiniBasePluginWidget
):
    '''Class representing a Validator widget

    .. note::

        _required_output a Boolean
    '''
