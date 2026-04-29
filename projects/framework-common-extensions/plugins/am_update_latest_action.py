# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_asset_manager.asset import constants as asset_const
from ftrack_framework_asset_manager.asset.ftrack_asset_info import (
    FtrackAssetInfo,
)


class AmUpdateLatestAction(BasePlugin):
    name = 'am_update_latest_action'

    def run(self, store):
        '''Get the latest version of an asset from ftrack.'''

        # Get asset_info data from store
        asset_info_data = store.get('asset_info') or store

        # Wrap in FtrackAssetInfo
        asset_info = FtrackAssetInfo(asset_info_data)

        # Extract required data
        asset_id = asset_info.get(asset_const.ASSET_ID)
        component_name = asset_info.get(asset_const.COMPONENT_NAME)

        if not asset_id or not component_name:
            self.logger.error(
                "Missing required data: asset_id or component_name"
            )
            return []

        # Query ftrack for the latest version
        query = (
            f'select is_latest_version, id, asset, components, components.name, '
            f'components.id, version, asset, asset.name, asset.type.name '
            f'from AssetVersion where asset.id is "{asset_id}" and '
            f'components.name is "{component_name}" and is_latest_version is "True"'
        )

        self.logger.debug(f"Querying ftrack: {query}")

        try:
            latest_version = self.session.query(query).one()
            new_version_id = latest_version['id']

            # Store the new version id
            store['new_version_id'] = new_version_id

            self.logger.debug(f"Found latest version: {new_version_id}")

            # Return the new version id in a list
            return [new_version_id]

        except Exception as e:
            self.logger.error(f"Error querying latest version: {e}")
            return []
