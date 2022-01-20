# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline.asset import FtrackAssetBase
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import base


class AssetManagerActionPlugin(base.BaseActionPlugin):
    '''
    Class representing a Asset Manager Action Plugin Inherits from
    :class:`~ftrack_connect_pipeline.plugin.base.BaseActionPlugin`
    '''

    return_type = list
    '''Type of object that should be returned'''
    plugin_type = constants.PLUGIN_AM_ACTION_TYPE
    '''Plugin type of the current plugin'''
    _required_output = []
    '''Expected output that should be returned'''
    ftrack_asset_class = FtrackAssetBase
    '''Define the class to use for the ftrack node to track the loaded assets'''

    def __init__(self, session):
        '''
        Initialise AssetManagerActionPlugin with instance of
        :class:`ftrack_api.session.Session`
        '''
        super(AssetManagerActionPlugin, self).__init__(session)
