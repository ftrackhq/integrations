# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants

class CommonUpdateLatestAssetManagerActionPlugin(BasePlugin):
    name = 'common_update_latest_am_action'
    host_type = constants.host.PYTHON_HOST_TYPE
    plugin_type = constants.plugin.PLUGIN_ACTION_TYPE

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=list,
            required_output_value=None
        )

    def run(self, context_data=None, data=None, options=None):
        '''Retrieve the latest version based on asset info passed with *data*'''
        # TODO: no need to convert or pass the asset info, we can simply query
        #  data.get('asset_id') and data.get('component_name')
        #  Somehow we should expose to the user what the arguments are and how
        #  are they filled out. Maybe exposing the engine in the doc so the user
        #  can see what each argument contain?


        asset_info = FtrackAssetInfo(data)

        query = (
            'select is_latest_version, id, asset, components, components.name, '
            'components.id, version, asset , asset.name, asset.type.name from '
            'AssetVersion where asset.id is "{}" and components.name is "{}"'
            'and is_latest_version is "True"'
        ).format(
            asset_info[constants.asset.ASSET_ID],
            asset_info[constants.asset.COMPONENT_NAME],
        )
        latest_version = self.session.query(query).one()

        return [latest_version['id']]
