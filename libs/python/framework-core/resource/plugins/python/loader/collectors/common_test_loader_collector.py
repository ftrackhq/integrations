# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import plugin
import ftrack_api


class CommonTestOpenerCollectorPlugin(plugin.LoaderCollectorPlugin):
    plugin_name = 'common_test_opener_collector'
    '''Opener collector test/template plugin'''

    def run(self, context_data=None, data=None, options=None):
        return []


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = CommonTestOpenerCollectorPlugin(api_object)
    plugin.register()
