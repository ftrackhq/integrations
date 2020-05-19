# # :coding: utf-8
# # :copyright: Copyright (c) 2019 ftrack
#
from ftrack_connect_pipeline.constants.asset import v1, v2
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo
import logging

class FtrackAssetBase(object):
    '''
        Base FtrackAssetBase class.
    '''

    @property
    def asset_info(self):
        return self._asset_info

    @property
    def session(self):
        return self._session

    def __init__(self, ftrack_asset_info, session):
        '''
        Initialize FtrackAssetBase with *ftrack_asset_info*, and *session*.

        *ftrack_asset_info* should be the
        :class:`ftrack_connect_pipeline.asset.asset_info.FtrackAssetInfo`
        instance.
        *session* should be the :class:`ftrack_api.session.Session` instance
        to use for communication with the server.
        '''
        if not isinstance(ftrack_asset_info, FtrackAssetInfo):
            raise TypeError(
                "ftrack_asset_info argument has to be type of FtrackAssetInfo"
            )

        super(FtrackAssetBase, self).__init__()

        self.logger = logging.getLogger(__name__)

        self._asset_info = ftrack_asset_info
        self.logger.debug("Asset info assigned: {}".format(self._asset_info))
        self._session = session

    # def get_version
    # def set_version
