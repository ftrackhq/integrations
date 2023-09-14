# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants

from ftrack_framework_core.asset.asset_info import FtrackAssetInfo


class CommonTestAssetManagerSelectActionPlugin(BasePlugin):
    name = 'common_test_select_am_action'
    host_type = constants.host.PYTHON_HOST_TYPE
    plugin_type = constants.plugin.PLUGIN_ACTION_TYPE

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=bool,
            required_output_value=None,
        )

    def run(self, context_data=None, data=None, options=None):
        '''This just a test example of an asset manager select plugin that mocks
        selection of DCC assets, provided in *context_data*, in the scene'''

        assert context_data, 'No asset provided!'

        asset_info = FtrackAssetInfo(context_data['asset_info'])

        status = constants.status.SUCCESS_STATUS

        print('Mock selecting asset: {}'.format(asset_info))

        if status == constants.status.SUCCESS_STATUS:
            return True
        else:
            return False, {
                'message': 'Could not mock select asset(s) {}!'.format(
                    context_data
                )
            }
