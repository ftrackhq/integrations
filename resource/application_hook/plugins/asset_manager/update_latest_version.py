# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import ftrack_api
from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo
from ftrack_connect_pipeline.constants import asset as constants


class UpdateLatestPlugin(plugin.AssetManagerActionPlugin):
    plugin_name = 'update_latest'

    def run(self, context=None, data=None, options=None):
        asset_info = FtrackAssetInfo(data)

        query = (
            'select is_latest_version, id, asset, components, components.name, '
            'components.id, version, asset , asset.name, asset.type.name from '
            'AssetVersion where asset.id is "{}" and components.name is "{}"'
            'and is_latest_version is "True"'
        ).format(
            asset_info[constants.ASSET_ID], asset_info[constants.COMPONENT_NAME]
        )
        latest_version = self.session.query(query).one()

        return [latest_version['id']]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UpdateLatestPlugin(api_object)
    plugin.register()
