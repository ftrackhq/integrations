# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import ftrack_api
from ftrack_connect_pipeline_3dsmax import plugin
from ftrack_connect_pipeline_3dsmax.constants import asset as asset_const
from ftrack_connect_pipeline_3dsmax.utils import custom_commands as max_utils


class SelectAssetMaxPlugin(plugin.AssetManagerMenuActionMaxPlugin):
    plugin_name = 'select_asset'

    def run(self, context=None, data=None, options=None):
        ftrack_asset_class = data
        if options.get('clear_selection'):
            max_utils.deselect_all()

        max_utils.deselect_all()
        #TODO: check if I have to get the object or not needed
        #ftrack_object = ftrack_asset_class.ftrack_object.Object
        max_utils.add_all_children_to_selection(
            ftrack_asset_class.ftrack_object
        )

        return []


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = SelectAssetMaxPlugin(api_object)
    plugin.register()
