from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline_maya.plugin import BaseMayaPlugin, BaseMayaWidget


# PLUGINS
class CollectorMayaPlugin(BaseMayaPlugin):
    plugin_type = constants.COLLECTORS


class ValidatorMayaPlugin(BaseMayaPlugin):
    plugin_type = constants.VALIDATORS


class ExtractorMayaPlugin(BaseMayaPlugin):
    plugin_type = constants.EXTRACTORS


class PublisherMayaPlugin(BaseMayaPlugin):
    plugin_type = constants.PUBLISHERS


# WIDGET
class CollectorMayaWidget(BaseMayaWidget):
    plugin_type = constants.COLLECTORS


class ValidatorMayaWidget(BaseMayaWidget):
    plugin_type = constants.VALIDATORS


class ExtractorMayaWidget(BaseMayaWidget):
    plugin_type = constants.EXTRACTORS


class PublisherMayaWidget(BaseMayaWidget):
    plugin_type = constants.PUBLISHERS
