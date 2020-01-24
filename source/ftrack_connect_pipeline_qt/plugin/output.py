# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline_qt.plugin import BasePluginWidget


class OutputWidget(BasePluginWidget):
    plugin_type = constants.PLUGIN_OUTPUT_TYPE
