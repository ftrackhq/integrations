# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import ftrack_api
from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_nuke.asset import FtrackAssetTab
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo
from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils


class DiscoverAssetsNukePlugin(plugin.AssetManagerDiscoverNukePlugin):
    plugin_name = 'discover_assets'

    def run(self, context=None, data=None, options=None):

        ftrack_asset_nodes = nuke_utils.get_nodes_with_ftrack_tab()
        ftrack_asset_info_list = []

        for ftrack_object in ftrack_asset_nodes:
            param_dict = FtrackAssetTab.get_parameters_dictionary(
                ftrack_object
            )
            node_asset_info = FtrackAssetInfo(param_dict)
            ftrack_asset_info_list.append(node_asset_info)

        ftrack_asset_list = []

        for asset_info in ftrack_asset_info_list:
            ftrack_asset_class = FtrackAssetTab(self.event_manager)
            ftrack_asset_class.asset_info = asset_info
            ftrack_asset_class.init_ftrack_object()
            ftrack_asset_list.append(ftrack_asset_class)

        return ftrack_asset_list


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = DiscoverAssetsNukePlugin(api_object)
    plugin.register()
