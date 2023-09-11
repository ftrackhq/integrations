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
            required_output_type=list,
            required_output_value=None
        )

    def run(self, context_data=None, data=None, options=None):
        '''This just a test example of an asset manager select plugin that mocks
        selection of a DCC asset in the scene'''

        status = constants.status.SUCCESS_STATUS

        print(
            'Mock selecting asset: {}'.format(
                len(data)
            )
        )

        if status == constants.status.SUCCESS_STATUS:
            return data
        else:
            return False, {
                'message': 'Could not gather mock assets from ftrack!'
            }
