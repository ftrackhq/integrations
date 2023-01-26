# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import base


class LoaderCollectorPlugin(base.BaseCollectorPlugin):
    '''
    Base Loader Collector Plugin Class inherits from
    :class:`~ftrack_connect_pipeline.plugin.base.BaseCollectorPlugin`
    '''

    return_type = dict
    '''Required return type'''
    plugin_type = constants.PLUGIN_LOADER_COLLECTOR_TYPE
    '''Type of the plugin'''
    _required_output = []
    '''Required return exporters'''

    def __init__(self, session):
        super(LoaderCollectorPlugin, self).__init__(session)
