# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import ftrack_api
from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo


class UpdateLatestPlugin(plugin.AssetManagerActionPlugin):
    plugin_name = 'update_latest'

    def run(self, context=None, data=None, options=None):
        asset_info = FtrackAssetInfo(data)
        latest_version = asset_info['versions'][-1]

        return [latest_version['id']]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UpdateLatestPlugin(api_object)
    plugin.register()
