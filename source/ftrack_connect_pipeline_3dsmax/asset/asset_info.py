# # :coding: utf-8
# # :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo


class FtrackAssetInfoMax(FtrackAssetInfo):
    '''
    Base FtrackAssetInfoMax class.
    '''

    def __init__(self, mapping, **kwargs):
        '''
        Initialize the FtrackAssetInfoMax with the given *mapping*.

        *mapping* Dictionary with the current asset information.
        '''

        super(FtrackAssetInfoMax, self).__init__(mapping, **kwargs)

