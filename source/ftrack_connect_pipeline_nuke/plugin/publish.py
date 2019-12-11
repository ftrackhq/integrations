# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline_qt import plugin as pluginWidget
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
class CollectorNukeWidget(BaseNukeWidget, pluginWidget.CollectorWidget):
    plugin_type = constants.COLLECT


class ValidatorNukeWidget(BaseNukeWidget, pluginWidget.ValidatorWidget):
    plugin_type = constants.VALIDATE


class OutputNukeWidget(BaseNukeWidget, pluginWidget.OutputWidget):
    plugin_type = constants.OUTPUT


class PublisherNukeWidget(BaseNukeWidget, pluginWidget.PublisherWidget):
    plugin_type = constants.PUBLISH
