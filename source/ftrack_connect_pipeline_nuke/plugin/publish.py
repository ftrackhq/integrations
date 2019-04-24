# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants, plugin
from ftrack_connect_pipeline_nuke.plugin import BaseNukePlugin, BaseNukeWidget


# PLUGINS
class CollectorNukePlugin(BaseNukePlugin, plugin.CollectorPlugin):
    plugin_type = constants.COLLECT


class ValidatorNukePlugin(BaseNukePlugin, plugin.ValidatorPlugin):
    plugin_type = constants.VALIDATE


class OutputNukePlugin(BaseNukePlugin, plugin.OutputPlugin):
    plugin_type = constants.OUTPUT


class PublisherNukePlugin(BaseNukePlugin, plugin.PublisherPlugin):
    plugin_type = constants.PUBLISH


# WIDGET
class CollectorNukeWidget(BaseNukeWidget, plugin.CollectorWidget):
    plugin_type = constants.COLLECT


class ValidatorNukeWidget(BaseNukeWidget, plugin.ValidatorWidget):
    plugin_type = constants.VALIDATE


class OutputNukeWidget(BaseNukeWidget, plugin.OutputWidget):
    plugin_type = constants.OUTPUT


class PublisherNukeWidget(BaseNukeWidget, plugin.PublisherWidget):
    plugin_type = constants.PUBLISH
