# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline_maya.plugin import BaseMayaPlugin, BaseMayaWidget


# PLUGINS
class CollectorMayaPlugin(BaseMayaPlugin):
    plugin_type = constants.COLLECT


class ValidatorMayaPlugin(BaseMayaPlugin):
    plugin_type = constants.VALIDATE


class ExtractorMayaPlugin(BaseMayaPlugin):
    plugin_type = constants.OUTPUT


class PublisherMayaPlugin(BaseMayaPlugin):
    plugin_type = constants.PUBLISH


# WIDGET
class CollectorMayaWidget(BaseMayaWidget):
    plugin_type = constants.COLLECT


class ValidatorMayaWidget(BaseMayaWidget):
    plugin_type = constants.VALIDATE


class ExtractorMayaWidget(BaseMayaWidget):
    plugin_type = constants.OUTPUT


class PublisherMayaWidget(BaseMayaWidget):
    plugin_type = constants.PUBLISH
