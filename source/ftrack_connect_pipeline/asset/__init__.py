# # :coding: utf-8
# # :copyright: Copyright (c) 2019 ftrack
#

import logging
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo, asset_info_from_ftrack_version
from ftrack_connect_pipeline.constants import asset as constants


class FtrackAssetBase(object):
    '''
        Base FtrackAssetBase class.
    '''

    identity = None
    default_component_name = 'main'

    def is_ftrack_node(self, other):
        raise NotImplementedError()

    @property
    def component_name(self):
        return self.asset_info.get(constants.COMPONENT_NAME, self.default_component_name)

    @property
    def asset_versions(self):
        query = (
            'select id, asset, components, components.name, components.id, version, asset , asset.name, asset.type.name from '
            'AssetVersion where asset.id is "{}" and components.name is "{}"'
            'order by version ascending'
        ).format(
            self.asset_info[constants.ASSET_ID], self.component_name
        )
        versions = self.session.query(query).all()
        return versions

    @property
    def ftrack_version(self):
        asset_version = self.session.get(
            'AssetVersion', self.asset_info[constants.VERSION_ID]
        )
        return asset_version

    @property
    def is_latest(self):
        return self.ftrack_version['is_latest_version']

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
        self._session = session

        self._nodes = []
        self._node = None

    def _set_node(self, ftrack_node):
        '''
        Sets the given *ftrack_node* as the current self.node of the class
        '''
        self._node = ftrack_node

    def change_version(self, asset_version_id):
        asset_version = self.session.get('AssetVersion', asset_version_id)
        asset_info = asset_info_from_ftrack_version(asset_version, self.component_name)
        self.asset_info.update(asset_info)
