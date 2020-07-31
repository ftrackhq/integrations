# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import nuke
import ftrack_api
from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_nuke.constants import asset as asset_const
from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils


class SelectAssetNukePlugin(plugin.AssetManagerMenuActionNukePlugin):
    plugin_name = 'select_asset'

    def run(self, context=None, data=None, options=None):
        ftrack_asset_class = data
        if options.get('clear_selection'):
            nuke_utils.cleanSelection()

        ftrack_object = nuke.toNode(ftrack_asset_class.ftrack_object)

        parented_nodes = ftrack_object.getNodes()
        parented_nodes_names = [x.knob('name').value() for x in parented_nodes]
        nodes_to_select_str = ftrack_object.knob(
            asset_const.ASSET_LINK
        ).value()
        nodes_to_select = nodes_to_select_str.split(";")
        nodes_to_select = set(nodes_to_select + parented_nodes_names)

        for node_s in nodes_to_select:
            node = nuke.toNode(node_s)
            node['selected'].setValue(True)

        ftrack_object['selected'].setValue(True)

        return []


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = SelectAssetNukePlugin(api_object)
    plugin.register()
