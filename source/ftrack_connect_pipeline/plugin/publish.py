from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import BasePlugin, BaseWidget


# PLUGINS
class CollectorPlugin(BasePlugin):
    plugin_type = constants.COLLECTORS


class ValidatorPlugin(BasePlugin):
    plugin_type = constants.VALIDATORS


class ExtractorPlugin(BasePlugin):
    plugin_type = constants.EXTRACTORS


class PublisherPlugin(BasePlugin):
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
