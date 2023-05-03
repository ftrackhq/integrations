# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import plugin
import ftrack_api


class CommonTestPublisherCollectorPlugin(plugin.PublisherCollectorPlugin):
    '''Publisher collector test/template plugin'''

    plugin_name = 'common_test_publisher_collector'

    def run(self, context_data=None, data=None, options=None):
        '''Empty collector'''
        return []


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = CommonTestPublisherCollectorPlugin(api_object)
    plugin.register()
