# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_harmony.plugin import (
    HarmonyBasePlugin,
    HarmonyBasePluginWidget,
)


class HarmonyPublisherValidatorPlugin(
    plugin.PublisherValidatorPlugin, HarmonyBasePlugin
):
    '''Class representing a Validator Plugin

    .. note::

        _required_output a Boolean
    '''


class HarmonyPublisherValidatorPluginWidget(
    pluginWidget.PublisherValidatorPluginWidget, HarmonyBasePluginWidget
):
    '''Class representing a Validator widget

    .. note::

        _required_output a Boolean
    '''
