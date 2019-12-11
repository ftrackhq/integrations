# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin, constants
from ftrack_connect_pipeline_3dsmax.plugin import BaseMaxPlugin, BaseMaxWidget


# PLUGINS
class CollectorMaxPlugin(BaseMaxPlugin, plugin.CollectorPlugin):
    plugin_type = constants.COLLECTORS


class ValidatorMaxPlugin(BaseMaxPlugin, plugin.ValidatorPlugin):
    plugin_type = constants.VALIDATORS


class OutputMaxPlugin(BaseMaxPlugin, plugin.OutputPlugin):
    plugin_type = constants.OUTPUTS


class PublisherMaxPlugin(BaseMaxPlugin, plugin.PublisherPlugin):
    plugin_type = constants.PUBLISHERS


# WIDGET
class CollectorMaxWidget(BaseMaxWidget, plugin.CollectorWidget):
    plugin_type = constants.COLLECTORS


class ValidatorMaxWidget(BaseMaxWidget, plugin.ValidatorWidget):
    plugin_type = constants.VALIDATORS


class OutputMaxWidget(BaseMaxWidget, plugin.OutputWidget):
    plugin_type = constants.OUTPUTS


class PublisherMaxWidget(BaseMaxWidget, plugin.PublisherWidget):
    plugin_type = constants.PUBLISHERS
