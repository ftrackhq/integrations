# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import os
from ftrack_connect_pipeline import plugin
import ftrack_api


class CommonPassthroughPublisherFinalizerPlugin(
    plugin.PublisherFinalizerPlugin
):
    '''Empty/passthrough publisher finalizer plugin'''

    plugin_name = 'common_passthrough_publisher_finalizer'

    def run(self, context_data=None, data=None, options=None):
        return {}


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = CommonPassthroughPublisherFinalizerPlugin(api_object)
    plugin.register()
