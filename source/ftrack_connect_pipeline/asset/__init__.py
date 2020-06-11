# # :coding: utf-8
# # :copyright: Copyright (c) 2019 ftrack
#

import logging
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo
from ftrack_connect_pipeline.constants import asset as constants


class FtrackAssetBase(object):
    '''
        Base FtrackAssetBase class.
    '''

    identity = None

    def is_ftrack_node(self, other):
        raise NotImplementedError()

    @property
    def asset_info(self):
        return self._asset_info

    @property
    def session(self):
        return self._session

    @property
    def nodes(self):
        return self._nodes[:]

    @property
    def node(self):
        return self._node

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

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self._asset_info = ftrack_asset_info
        self.logger.debug("Asset info assigned: {}".format(self._asset_info))
        self._session = session

        self._nodes = []
        self._node = None

    def _set_node(self, ftrack_node):
        '''
        Sets the given *ftrack_node* as the current self.node of the class
        '''
        self._node = ftrack_node

    def get_available_asset_versions(self):
        asset = self.session.get('Asset', self.asset_info['asset_id'])
        return asset['versions']

    def change_version(self, asset_version_id):
        asset_info_data = {}
        asset_version = self.session.get('AssetVersion', asset_version_id)

        asset = asset_version['asset']
        asset_info_data[constants.ASSET_NAME] = asset['name']
        asset_info_data[constants.ASSET_TYPE] = asset['type']['name']
        asset_info_data[constants.ASSET_ID] = asset['id']
        asset_info_data[constants.VERSION_NUMBER] = int(asset_version['version'])
        asset_info_data[constants.VERSION_ID] = asset_version['id']

        location = self.session.pick_location()

        for component in asset_version['components']:
            if location.get_component_availability(component) < 100.0:
                continue
            component_path = location.get_filesystem_path(component)
            if component_path:
                asset_info_data[constants.COMPONENT_NAME] = component['name']
                asset_info_data[constants.COMPONENT_ID] = component['id']
                asset_info_data[constants.COMPONENT_PATH] = component_path

        self.asset_info.update(asset_info_data)