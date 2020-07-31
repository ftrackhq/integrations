# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import ftrack_api
from ftrack_connect_pipeline_3dsmax import plugin
from ftrack_connect_pipeline_3dsmax.utils import custom_commands as max_utils


class RemoveAssetMaxPlugin(plugin.AssetManagerMenuActionMaxPlugin):
    plugin_name = 'remove_asset'

    def run(self, context=None, data=None, options=None):
        ftrack_asset_class = data

        # TODO: check if I have to get the object or not needed
        #ftrack_object = ftrack_asset_class.ftrack_object.Object
        max_utils.delete_all_children(ftrack_asset_class.ftrack_object)
        ftrack_asset_class.ftrack_object.Delete()

        return []


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = RemoveAssetMaxPlugin(api_object)
    plugin.register()
