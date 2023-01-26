# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import base


class OpenerCollectorPlugin(base.BaseCollectorPlugin):
    '''
    Base Opener Collector Plugin Class inherits from
    :class:`~ftrack_connect_pipeline.plugin.base.BaseCollectorPlugin`
    '''

    return_type = dict
    '''Required return type'''
    plugin_type = constants.PLUGIN_OPENER_COLLECTOR_TYPE
    '''Type of the plugin'''
    _required_output = []
    '''Required return exporters'''

    def __init__(self, session):
        super(OpenerCollectorPlugin, self).__init__(session)
