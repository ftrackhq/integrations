# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline_3dsmax.plugin import BaseMaxPlugin, BaseMaxWidget


# PLUGINS
class CollectorMaxPlugin(BaseMaxPlugin):
    plugin_type = constants.COLLECT


class ValidatorMaxPlugin(BaseMaxPlugin):
    plugin_type = constants.VALIDATE


class ExtractorMaxPlugin(BaseMaxPlugin):
    plugin_type = constants.OUTPUT


class PublisherMaxPlugin(BaseMaxPlugin):
    plugin_type = constants.PUBLISH


# WIDGET
class CollectorMaxWidget(BaseMaxWidget):
    plugin_type = constants.COLLECT


class ValidatorMaxWidget(BaseMaxWidget):
    plugin_type = constants.VALIDATE


class ExtractorMaxWidget(BaseMaxWidget):
    plugin_type = constants.OUTPUT


class PublisherMaxWidget(BaseMaxWidget):
    plugin_type = constants.PUBLISH
