# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline_qt.plugin import BasePluginWidget

# WIDGET
class CollectorWidget(BasePluginWidget):
    plugin_type = constants.COLLECTORS


class ValidatorWidget(BasePluginWidget):
    plugin_type = constants.VALIDATORS


class OutputWidget(BasePluginWidget):
    plugin_type = constants.OUTPUTS


class PublisherWidget(BasePluginWidget):
    plugin_type = constants.PUBLISHERS
