# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from framework_core.constants import plugin
from framework_qt.plugin import BasePluginWidget


class BaseCollectorPluginWidget(BasePluginWidget):
    '''
    Base Collector Widget Class inherits from
    :class:`~framework_qt.plugin.BasePluginWidget`
    '''

    plugin_type = plugin._PLUGIN_COLLECTOR_TYPE
    '''Type of the plugin'''
