# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline_nuke.plugin import BaseNukePlugin, BaseNukeWidget


# PLUGINS
class CollectorNukePlugin(BaseNukePlugin):
    plugin_type = constants.COLLECT


class ValidatorNukePlugin(BaseNukePlugin):
    plugin_type = constants.VALIDATE


class ExtractorNukePlugin(BaseNukePlugin):
    plugin_type = constants.OUTPUT


class PublisherNukePlugin(BaseNukePlugin):
    plugin_type = constants.PUBLISH


# WIDGET
class CollectorNukeWidget(BaseNukeWidget):
    plugin_type = constants.COLLECT


class ValidatorNukeWidget(BaseNukeWidget):
    plugin_type = constants.VALIDATE


class ExtractorNukeWidget(BaseNukeWidget):
    plugin_type = constants.OUTPUT


class PublisherNukeWidget(BaseNukeWidget):
    plugin_type = constants.PUBLISH
