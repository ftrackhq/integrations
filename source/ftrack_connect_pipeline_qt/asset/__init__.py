# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline.asset import FtrackAssetBase
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo

#TODO: Note: in order to make this work should exists a host engine to run this
# FtrackASsetQt class.


class FtrackAssetQt(FtrackAssetBase):
    '''
    Base FtrackAssetQt class.
    '''

    def __init__(self, event_manager):
        '''
        Initialize FtrackAssetQt with *event_manager*
        '''
        super(FtrackAssetQt, self).__init__(event_manager)

    def _change_version(self, event):
        asset_info = event['data']

        if not asset_info:
            self.logger.warning("Asset version couldn't change")
            return
        if not isinstance(asset_info, FtrackAssetInfo):
            raise TypeError(
                "return type of change version has to be type of FtrackAssetInfo"
            )

        self.asset_info.update(asset_info)

        return asset_info