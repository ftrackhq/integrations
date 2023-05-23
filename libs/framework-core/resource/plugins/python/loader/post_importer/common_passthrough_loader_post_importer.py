# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_framework_core import plugin
import ftrack_api


class CommonPassthroughLoaderPostImporterPlugin(
    plugin.LoaderPostImporterPlugin
):
    '''Empty/passthrough loader post importer plugin'''

    plugin_name = 'common_passthrough_loader_post_importer'

    def run(self, context_data=None, data=None, options=None):
        return {}


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = CommonPassthroughLoaderPostImporterPlugin(api_object)
    plugin.register()
