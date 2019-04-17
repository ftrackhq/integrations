# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline_nuke.plugin import BasenukePlugin, BasenukeWidget


# PLUGINS
class CollectorNukePlugin(BasenukePlugin):
    plugin_type = constants.COLLECT


class ValidatorNukePlugin(BasenukePlugin):
    plugin_type = constants.VALIDATE


class ExtractorNukePlugin(BasenukePlugin):
    plugin_type = constants.OUTPUT


class PublisherNukePlugin(BasenukePlugin):
    plugin_type = constants.PUBLISH


# WIDGET
class CollectorNukeWidget(BasenukeWidget):
    plugin_type = constants.COLLECT


class ValidatorNukeWidget(BasenukeWidget):
    plugin_type = constants.VALIDATE


class ExtractorNukeWidget(BasenukeWidget):
    plugin_type = constants.OUTPUT


class PublisherNukeWidget(BasenukeWidget):
    plugin_type = constants.PUBLISH
