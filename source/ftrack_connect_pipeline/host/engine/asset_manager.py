# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import copy
import ftrack_api

from ftrack_connect_pipeline.host.engine import BaseEngine
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.asset import FtrackAssetBase, asset_info_from_ftrack_version


class AssetManagerEngine(BaseEngine):
    engine_type = 'asset_manager'
    ftrack_asset_class = FtrackAssetBase

    def __init__(self, event_manager, host, hostid):
        '''Initialise AssetManagerEngine with *event_manager*, *host*, *hostid*
        and *asset_type*'''
        super(AssetManagerEngine, self).__init__(
            event_manager, host, hostid, asset_type=None
        )

        self.ftrack_asset_base = self.ftrack_asset_class(self.event_manager)


    def discover_assets(self, data):
        #TODO: add ftrackassetbase as a class variable in order to use the
        # ftrackmayanode in case of maya

        ftrack_asset_info_list = self.ftrack_asset_base.discover_assets()
        ftrack_asset_list = []

        for asset_info in ftrack_asset_info_list:
            ftrack_asset_class = self.ftrack_asset_class(self.event_manager)
            ftrack_asset_class.set_asset_info(asset_info)
            ftrack_asset_class.init_node()
            ftrack_asset_list.append(ftrack_asset_class)

        return ftrack_asset_list

    def change_asset_version(self, data):
        asset_info = data['data']
        return asset_info