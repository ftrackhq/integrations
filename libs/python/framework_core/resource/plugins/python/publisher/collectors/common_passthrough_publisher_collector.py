# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
import ftrack_api


class CommonPassthroughPublisherCollectorPlugin(
    plugin.PublisherCollectorPlugin
):
    '''Empty publisher collector plugin'''

    plugin_name = 'common_passthrough_publisher_collector'

    def run(self, context_data=None, data=None, options=None):
        return []


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = CommonPassthroughPublisherCollectorPlugin(api_object)
    plugin.register()
