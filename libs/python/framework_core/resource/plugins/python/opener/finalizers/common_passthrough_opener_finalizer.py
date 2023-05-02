# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from framework_core import plugin
import ftrack_api


class CommonPassthroughOpenerFinalizerPlugin(plugin.OpenerFinalizerPlugin):
    '''Empty/passthrough opener finalizer plugin'''

    plugin_name = 'common_passthrough_opener_finalizer'

    def run(self, context_data=None, data=None, options=None):
        return {}


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = CommonPassthroughOpenerFinalizerPlugin(api_object)
    plugin.register()
