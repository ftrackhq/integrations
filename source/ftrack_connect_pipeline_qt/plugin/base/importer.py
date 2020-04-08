# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline.constants import plugin
from ftrack_connect_pipeline_qt.plugin import BasePluginWidget


class BaseImporterWidget(BasePluginWidget):
    ''' Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
    plugin_type = plugin._PLUGIN_IMPORTER_TYPE

