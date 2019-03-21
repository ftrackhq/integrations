# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import BasePlugin, BaseWidget


# PLUGINS
class CollectorPlugin(BasePlugin):
    return_type = list
    plugin_type = constants.COLLECTORS


class ValidatorPlugin(BasePlugin):
    return_type = bool
    plugin_type = constants.VALIDATORS


class ExtractorPlugin(BasePlugin):
    return_type = dict
    plugin_type = constants.EXTRACTORS


class PublisherPlugin(BasePlugin):
    return_type = list
    plugin_type = constants.PUBLISHERS


# WIDGET
class CollectorWidget(BaseWidget):
    plugin_type = constants.COLLECTORS


class ValidatorWidget(BaseWidget):
    plugin_type = constants.VALIDATORS


class ExtractorWidget(BaseWidget):
    plugin_type = constants.EXTRACTORS


class PublisherWidget(BaseWidget):
    plugin_type = constants.PUBLISHERS
