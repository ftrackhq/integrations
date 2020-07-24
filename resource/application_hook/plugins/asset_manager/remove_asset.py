# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import ftrack_api
from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline.asset import FtrackAssetBase
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo



class RemoveAssetPlugin(plugin.AssetManagerMenuActionPlugin):
    plugin_name = 'remove_asset'

    def run(self, context=None, data=None, options=None):
        ftrack_asset_class = data
        return []


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = RemoveAssetPlugin(api_object)
    plugin.register()
