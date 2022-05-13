# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline.constants import plugin
from ftrack_connect_pipeline_qt.plugin import BasePluginWidget


class BasePostImporterPluginWidget(BasePluginWidget):
    '''
    Base Post Import Widget Class inherits from
    :class:`~ftrack_connect_pipeline_qt.plugin.BasePluginWidget`
    '''

    plugin_type = plugin._PLUGIN_POST_IMPORTER_TYPE
