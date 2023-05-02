# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from framework_core import constants
from framework_core.plugin import base


class PublisherCollectorPlugin(base.BaseCollectorPlugin):
    '''
    Base Publisher Collector Plugin Class inherits from
    :class:`~framework_core.plugin.base.BaseCollectorPlugin`
    '''

    return_type = list
    '''Required return type'''
    plugin_type = constants.PLUGIN_PUBLISHER_COLLECTOR_TYPE
    '''Type of the plugin'''
    _required_output = []
    '''Required return exporters'''

    def __init__(self, session):
        super(PublisherCollectorPlugin, self).__init__(session)
