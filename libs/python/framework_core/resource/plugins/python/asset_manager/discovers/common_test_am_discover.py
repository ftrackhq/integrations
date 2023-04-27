# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import ftrack_api
from ftrack_connect_pipeline import plugin


class CommonTestAssetManagerDiscoverPlugin(plugin.AssetManagerDiscoverPlugin):
    plugin_name = 'common_test_am_discover'

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
