## :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import plugin
import ftrack_api


class CommonPassthroughOpenerPostFinalizerPlugin(
    plugin.OpenerPostFinalizerPlugin
):
    '''Empty/passthrough opener post finalizer plugin'''

    plugin_name = 'common_passthrough_opener_post_finalizer'

    def run(self, context_data=None, data=None, options=None):
        return {}


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = CommonPassthroughOpenerPostFinalizerPlugin(api_object)
    plugin.register()
