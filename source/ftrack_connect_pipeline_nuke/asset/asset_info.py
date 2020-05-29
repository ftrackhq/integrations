# # :coding: utf-8
# # :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo


class FtrackAssetInfoNuke(FtrackAssetInfo):
    '''
    Base FtrackAssetInfoMaya class.
    '''

    def __init__(self, mapping, **kwargs):
        '''
        Initialize the FtrackAssetInfoMaya with the given *mapping*.

        *mapping* Dictionary with the current asset information.

        ..note:: Override the init in case we want to add special keys for maya.
        '''

        super(FtrackAssetInfoNuke, self).__init__(mapping, **kwargs)

