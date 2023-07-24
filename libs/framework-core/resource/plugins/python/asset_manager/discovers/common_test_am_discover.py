# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_framework_plugin import BasePlugin
from ftrack_framework_plugin import constants


class CommonTestAssetManagerDiscoverPlugin(BasePlugin):
    plugin_name = 'common_test_am_discover'
    host_type = constants.hosts.PYTHON_HOST_TYPE
    plugin_type = constants.PLUGIN_DISCOVER_TYPE

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=list,
            required_output_value=None
        )

    def run(self, context_data=None, data=None, options=None):
        '''This just an test example of an asset manager discovery plugin'''
        filter = {'asset_name': 'torso', 'asset_type_name': 'geo'}
        return filter


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = CommonTestAssetManagerDiscoverPlugin(api_object)
    plugin.register()
