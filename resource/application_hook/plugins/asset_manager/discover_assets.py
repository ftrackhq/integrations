# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import ftrack_api
from ftrack_connect_pipeline_maya import plugin
from ftrack_connect_pipeline_maya.asset import FtrackAssetNode
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo
from ftrack_connect_pipeline_maya.utils import custom_commands as maya_utils


class DiscoverAssetsMayaPlugin(plugin.AssetManagerDiscoverMayaPlugin):
    plugin_name = 'discover_assets'

    def run(self, context=None, data=None, options=None):

        ftrack_asset_nodes = maya_utils.get_ftrack_nodes()
        ftrack_asset_info_list = []

        for ftrack_object in ftrack_asset_nodes:
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
    plugin = DiscoverAssetsMayaPlugin(api_object)
    plugin.register()
