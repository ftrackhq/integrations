# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import base
from ftrack_connect_pipeline.asset import FtrackAssetBase

class AssetManagerDiscoverPlugin(base.BaseDiscoverPlugin):
    '''
    Class representing a Asset Manager Discover Plugin
    '''
    return_type = list
    plugin_type = constants.PLUGIN_AM_DISCOVER_TYPE
    _required_output = []
    ftrack_asset_class = FtrackAssetBase

    def __init__(self, session):
        '''Initialise AssetManagerDiscoverPlugin with *session*

        *session* should be the :class:`ftrack_api.session.Session` instance
        to use for communication with the server.
        '''
        super(AssetManagerDiscoverPlugin, self).__init__(session)
