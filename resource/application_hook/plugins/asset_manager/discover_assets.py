# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import ftrack_api
from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline.asset import FtrackAssetBase
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo


class DiscoverAssetsPlugin(plugin.AssetManagerDiscoverPlugin):
    plugin_name = 'discover_assets'

    def run(self, context=None, data=None, options=None):

        component_name = 'main'
        versions = self.session.query(
            'select id, components, components.name, components.id, version, '
            'asset , asset.name, asset.type.name from AssetVersion where '
            'asset_id != None and components.name is "{0}" limit 10'.format(
                component_name
            )
        ).all()

        component_name = 'main'

        ftrack_asset_info_list = []

        for version in versions:
            asset_info = FtrackAssetInfo.from_ftrack_version(
                version, component_name
            )
            ftrack_asset_info_list.append(asset_info)

        ftrack_asset_list = []

        for asset_info in ftrack_asset_info_list:
            ftrack_asset_class = FtrackAssetBase(self.event_manager)
            ftrack_asset_class.asset_info = asset_info
            ftrack_asset_class.init_ftrack_object()
            ftrack_asset_list.append(ftrack_asset_class)

        return ftrack_asset_list


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = DiscoverAssetsPlugin(api_object)
    plugin.register()
