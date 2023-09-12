# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants

from ftrack_framework_core.asset.asset_info import FtrackAssetInfo


class CommonTestAssetManagerSelectActionPlugin(BasePlugin):
    name = 'common_test_select_am_action'
    host_type = constants.host.PYTHON_HOST_TYPE
    plugin_type = constants.plugin.PLUGIN_DISCOVER_TYPE

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=bool,
            required_output_value=None,
        )

    def run_multiple(self, context_data=None, data=None, options=None):
        assert data and isinstance(data, list), 'No assets provided!'

        user_message = None
        status = constants.status.SUCCESS_STATUS

        for asset_info in data:
            item_result = self.run(context_data, asset_info, options)

            if isinstance(item_result, tuple):
                if not item_result[0]:
                    status = constants.status.ERROR_STATUS
                    user_message = item_result[1]['message']
            elif not item_result:
                status = constants.status.ERROR_STATUS
                user_message = '-unknown error-'

        if status == constants.status.SUCCESS_STATUS:
            return True
        else:
            return False, {
                'message': 'Could not mock select {} asset(s): {}!'.format(
                    len(data), user_message
                )
            }

    def run(self, context_data=None, data=None, options=None):
        '''This just a test example of an asset manager select plugin that mocks
        selection of a DCC asset in the scene'''

        assert data, 'No asset provided!'

        status = constants.status.SUCCESS_STATUS

        asset_info = data

        print('Mock selecting asset: {}'.format(len(asset_info)))

        if status == constants.status.SUCCESS_STATUS:
            return True
        else:
            return False, {
                'message': 'Could not mock select asset {}!'.format(asset_info)
            }
