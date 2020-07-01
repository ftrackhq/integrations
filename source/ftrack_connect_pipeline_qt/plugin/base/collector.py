# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline.constants import plugin
from ftrack_connect_pipeline_qt.plugin import BasePluginWidget


class BaseCollectorWidget(BasePluginWidget):
    ''' Class representing a Collector Widget

    .. note::

        _required_output a List '''
    plugin_type = plugin._PLUGIN_COLLECTOR_TYPE

