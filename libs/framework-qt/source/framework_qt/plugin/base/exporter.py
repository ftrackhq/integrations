# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from framework_core.constants import plugin
from framework_qt.plugin import BasePluginWidget


class BaseExporterPluginWidget(BasePluginWidget):
    '''
    Base Exporter Widget Class inherits from
    :class:`~framework_qt.plugin.BasePluginWidget`
    '''

    plugin_type = plugin._PLUGIN_EXPORTER_TYPE
