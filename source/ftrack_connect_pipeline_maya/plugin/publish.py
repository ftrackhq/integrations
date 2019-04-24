# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin, constants
from ftrack_connect_pipeline_maya.plugin import BaseMayaPlugin, BaseMayaWidget


# PLUGINS
class CollectorMayaPlugin(BaseMayaPlugin, plugin.CollectorPlugin):
    plugin_type = constants.COLLECT


class ValidatorMayaPlugin(BaseMayaPlugin, plugin.ValidatorPlugin):
    plugin_type = constants.VALIDATE


class OutputMayaPlugin(BaseMayaPlugin, plugin.OutputPlugin):
    plugin_type = constants.OUTPUT


class PublisherMayaPlugin(BaseMayaPlugin, plugin.PublisherPlugin):
    plugin_type = constants.PUBLISH


# WIDGET
class CollectorMayaWidget(BaseMayaWidget, plugin.CollectorWidget):
    plugin_type = constants.COLLECT


class ValidatorMayaWidget(BaseMayaWidget, plugin.ValidatorWidget):
    plugin_type = constants.VALIDATE


class OutputMayaWidget(BaseMayaWidget, plugin.OutputWidget):
    plugin_type = constants.OUTPUT


class PublisherMayaWidget(BaseMayaWidget, plugin.PublisherWidget):
    plugin_type = constants.PUBLISH
