# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import ftrack_api

from ftrack_framework_core import plugin
from ftrack_framework_core.asset.asset_info import FtrackAssetInfo

from ftrack_framework_nuke import utils as nuke_utils
from ftrack_framework_nuke.asset import NukeFtrackObjectManager
from ftrack_framework_nuke.asset.dcc_object import NukeDccObject


class NukeDiscoverAssetManagerActionPlugin(plugin.AssetManagerActionPlugin):
    plugin_name = 'nuke_discover_am_action'

    FtrackObjectManager = NukeFtrackObjectManager
    '''FtrackObjectManager class to use'''
    DccObject = NukeDccObject
    '''DccObject class to use'''

    def run(self, context_data=None, data=None, options=None):
        '''Discover all the NUke assets in the scene'''

        ftrack_asset_node_names = [
            node.name() for node in nuke_utils.get_nodes_with_ftrack_tab()
        ]
        ftrack_asset_info_list = []

        if ftrack_asset_node_names:
            for node_name in ftrack_asset_node_names:
                param_dict = self.DccObject.dictionary_from_object(node_name)
                # avoid read and write nodes containing the old ftrack tab
                # without information
                if not param_dict:
                    continue
                node_asset_info = FtrackAssetInfo(param_dict)
                ftrack_asset_info_list.append(node_asset_info)

            if not ftrack_asset_info_list:
                return False, {
                    "message": "Could not load ftrack assets from the scene."
                }
        else:
            self.logger.debug("No assets in the scene")

        return ftrack_asset_info_list


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeDiscoverAssetManagerActionPlugin(api_object)
    plugin.register()
