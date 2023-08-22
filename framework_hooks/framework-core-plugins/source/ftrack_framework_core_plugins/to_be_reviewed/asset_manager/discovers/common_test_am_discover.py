# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants


class CommonTestAssetManagerDiscoverPlugin(BasePlugin):
    name = 'common_test_am_discover'
    host_type = constants.host.PYTHON_HOST_TYPE
    plugin_type = constants.plugin.PLUGIN_DISCOVER_TYPE

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=dict,
            required_output_value={
                'asset_name': None,
                'asset_type_name': None,
            },
        )

    def run(self, context_data=None, data=None, options=None):
        '''This just an test example of an asset manager discovery plugin'''
        filter = {'asset_name': 'torso', 'asset_type_name': 'geo'}
        return filter
