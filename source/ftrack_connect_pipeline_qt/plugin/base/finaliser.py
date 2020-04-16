# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline.constants import plugin
from ftrack_connect_pipeline_qt.plugin import BasePluginWidget


class BaseFinaliserWidget(BasePluginWidget):
    plugin_type = plugin._PLUGIN_FINALISER_TYPE
