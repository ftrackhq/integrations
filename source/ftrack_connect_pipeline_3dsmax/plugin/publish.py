# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin, constants
from ftrack_connect_pipeline_3dsmax.plugin import BaseMaxPlugin, BaseMaxWidget


# PLUGINS
class CollectorMaxPlugin(BaseMaxPlugin, plugin.CollectorPlugin):
    plugin_type = constants.COLLECT


class ValidatorMaxPlugin(BaseMaxPlugin, plugin.ValidatorPlugin):
    plugin_type = constants.VALIDATE


class ExtractorMaxPlugin(BaseMaxPlugin, plugin.OutputPlugin):
    plugin_type = constants.OUTPUT


class PublisherMaxPlugin(BaseMaxPlugin, plugin.PublisherPlugin):
    plugin_type = constants.PUBLISH


# WIDGET
class CollectorMaxWidget(BaseMaxWidget, plugin.CollectorWidget):
    plugin_type = constants.COLLECT


class ValidatorMaxWidget(BaseMaxWidget, plugin.ValidatorWidget):
    plugin_type = constants.VALIDATE


class ExtractorMaxWidget(BaseMaxWidget, plugin.OutputWidget):
    plugin_type = constants.OUTPUT


class PublisherMaxWidget(BaseMaxWidget, plugin.PublisherWidget):
    plugin_type = constants.PUBLISH
