# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants

from ftrack_framework_core.asset.asset_info import FtrackAssetInfo


class CommonQueryLatestAssetManagerActionPlugin(BasePlugin):
    name = 'common_query_latest_am_action'
    host_type = constants.host.PYTHON_HOST_TYPE
    plugin_type = constants.plugin.PLUGIN_ACTION_TYPE

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=list,
            required_output_value=None,
        )

    def run(self, context_data=None, data=None, options=None):
        '''Query the latest version based on asset info passed in *context_data*'''

        asset_info = FtrackAssetInfo(context_data['asset_info'])

        asset_id = asset_info[constants.asset.ASSET_ID]
        component_name = asset_info[constants.asset.COMPONENT_NAME]

        query = (
            'select is_latest_version, id, asset, components, components.name, '
            'components.id, version, asset , asset.name, asset.type.name from '
            'AssetVersion where asset.id is "{}" and components.name is "{}" '
            'and is_latest_version is "True" '
        ).format(
            asset_info[constants.asset.ASSET_ID],
            asset_info[constants.asset.COMPONENT_NAME],
        )
        latest_version = self.session.query(query).first()

        if latest_version:
            return [latest_version['id']]
        else:
            return False, {
                'message': 'No latest version found for asset_id: {}, '
                'component_name: {}'.format(asset_id, component_name)
            }
