# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants, plugin
from ftrack_connect_pipeline_nuke.plugin import BaseNukePlugin, BaseNukeWidget


# PLUGINS
class CollectorNukePlugin(BaseNukePlugin, plugin.CollectorPlugin):
    plugin_type = constants.COLLECTORS


class ValidatorNukePlugin(BaseNukePlugin, plugin.ValidatorPlugin):
    plugin_type = constants.VALIDATORS


class OutputNukePlugin(BaseNukePlugin, plugin.OutputPlugin):
    plugin_type = constants.OUTPUTS


class PublisherNukePlugin(BaseNukePlugin, plugin.PublisherPlugin):
    plugin_type = constants.PUBLISHERS


# WIDGET
class CollectorNukeWidget(BaseNukeWidget, plugin.CollectorWidget):
    plugin_type = constants.COLLECTORS


class ValidatorNukeWidget(BaseNukeWidget, plugin.ValidatorWidget):
    plugin_type = constants.VALIDATORS


class OutputNukeWidget(BaseNukeWidget, plugin.OutputWidget):
    plugin_type = constants.OUTPUTS


class PublisherNukeWidget(BaseNukeWidget, plugin.PublisherWidget):
    plugin_type = constants.PUBLISHERS
