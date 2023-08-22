# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_framework_core.constants import plugin
from ftrack_framework_qt.plugin import BasePluginWidget


class BasePostImporterPluginWidget(BasePluginWidget):
    '''
    Base Post Import Widget Class inherits from
    :class:`~ftrack_framework_qt.plugin.BasePluginWidget`
    '''

    plugin_type = plugin._PLUGIN_POST_IMPORTER_TYPE
