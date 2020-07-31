# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import ftrack_api
from ftrack_connect_pipeline_3dsmax import plugin
from ftrack_connect_pipeline_3dsmax.asset import FtrackAssetNode
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo
from ftrack_connect_pipeline_3dsmax.utils import custom_commands as max_utils


class DiscoverAssetsMaxPlugin(plugin.AssetManagerDiscoverMaxPlugin):
    plugin_name = 'discover_assets'

    def run(self, context=None, data=None, options=None):

        ftrack_asset_nodes = max_utils.get_ftrack_helpers()
        ftrack_asset_info_list = []

        for ftrack_object in ftrack_asset_nodes:
            obj = ftrack_object.Object
            param_dict = FtrackAssetNode.get_parameters_dictionary(
                ftrack_object
            )
            node_asset_info = FtrackAssetInfo(param_dict)
            ftrack_asset_info_list.append(node_asset_info)

        ftrack_asset_list = []

        for asset_info in ftrack_asset_info_list:
            ftrack_asset_class = FtrackAssetNode(self.event_manager)
            ftrack_asset_class.asset_info = asset_info
            ftrack_asset_class.init_ftrack_object()
            ftrack_asset_list.append(ftrack_asset_class)

        return ftrack_asset_list


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = DiscoverAssetsMaxPlugin(api_object)
    plugin.register()
