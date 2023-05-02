# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from framework_core import constants
from framework_core.plugin import base


class AssetManagerDiscoverPlugin(base.BaseDiscoverPlugin):
    '''
    Class representing a Asset Manager Action Plugin Inherits from
    :class:`~framework_core.plugin.base.BaseDiscoverPlugin`
    '''

    return_type = list
    '''Type of object that should be returned'''
    plugin_type = constants.PLUGIN_AM_DISCOVER_TYPE
    '''Plugin type of the current plugin'''
    _required_output = []
    '''Expected exporters that should be returned'''

    def __init__(self, session):
        '''
        Initialise AssetManagerDiscoverPlugin with instance of
        :class:`ftrack_api.session.Session`
        '''
        super(AssetManagerDiscoverPlugin, self).__init__(session)
