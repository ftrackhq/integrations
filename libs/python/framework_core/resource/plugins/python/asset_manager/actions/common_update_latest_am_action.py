# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import ftrack_api
from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo
from ftrack_connect_pipeline.constants import asset as constants


class CommonUpdateLatestAssetManagerActionPlugin(
    plugin.AssetManagerActionPlugin
):
    plugin_name = 'common_update_latest_am_action'

    def run(self, context_data=None, data=None, options=None):
        '''Retrieve the latest version based on asset info passed with *data*'''
        asset_info = FtrackAssetInfo(data)

        query = (
            'select is_latest_version, id, asset, components, components.name, '
            'components.id, version, asset , asset.name, asset.type.name from '
            'AssetVersion where asset.id is "{}" and components.name is "{}"'
            'and is_latest_version is "True"'
        ).format(
            asset_info[constants.ASSET_ID],
            asset_info[constants.COMPONENT_NAME],
        )
        latest_version = self.session.query(query).one()

        return [latest_version['id']]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = CommonUpdateLatestAssetManagerActionPlugin(api_object)
    plugin.register()
