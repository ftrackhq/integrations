# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_framework_core import plugin
from ftrack_framework_qt import plugin as pluginWidget
from ftrack_framework_maya.plugin import (
    MayaBasePlugin,
    MayaBasePluginWidget,
)


class MayaPublisherValidatorPlugin(
    plugin.PublisherValidatorPlugin, MayaBasePlugin
):
    '''Class representing a Validator Plugin

    .. note::

        _required_output a Boolean
    '''


class MayaPublisherValidatorPluginWidget(
    pluginWidget.PublisherValidatorPluginWidget, MayaBasePluginWidget
):
    '''Class representing a Validator widget

    .. note::

        _required_output a Boolean
    '''
