# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants
from ftrack_constants.framework import asset as asset_const
from ftrack_framework_core.asset.asset_info import FtrackAssetInfo


class CommonTestAssetManagerUnloadActionPlugin(BasePlugin):
    name = 'common_test_unload_am_action'
    host_type = constants.host.PYTHON_HOST_TYPE
    plugin_type = constants.plugin.PLUGIN_ACTION_TYPE

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=dict,
            required_output_value=None,
        )

    def run(self, context_data=None, data=None, options=None):
        '''This just a test example of an asset manager unload plugin that mocks
        unload of DCC assets, provided in *context_data*, in the scene'''

        assert context_data, 'No asset provided!'

        status = constants.status.SUCCESS_STATUS
        error_message = None

        asset_info = FtrackAssetInfo(context_data['asset_info'])

        if not asset_info[asset_const.OBJECTS_LOADED]:
            status = constants.status.ERROR_STATUS
            error_message = 'Asset {} is not loaded!'.format(
                asset_info[asset_const.ASSET_INFO_ID]
            )
        else:
            print('Mock unloading asset: {}'.format(asset_info))

        if status == constants.status.SUCCESS_STATUS:
            asset_info[asset_const.OBJECTS_LOADED] = False
            return asset_info.to_dict()
        else:
            return False, {
                'message': error_message
                or 'Could not unload asset: {}!'.format(context_data)
            }
