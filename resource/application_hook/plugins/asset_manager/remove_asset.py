# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import nuke
import ftrack_api
from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_nuke.constants import asset as asset_const


class RemoveAssetNukePlugin(plugin.AssetManagerMenuActionNukePlugin):
    plugin_name = 'remove_asset'

    def run(self, context=None, data=None, options=None):
        ftrack_asset_class = data

        ftrack_object = nuke.toNode(ftrack_asset_class.ftrack_object)
        if not ftrack_object:
            self.logger.info("There is no ftrack object")
            return

        if ftrack_object.Class() == 'BackdropNode':
            parented_nodes = ftrack_object.getNodes()
            parented_nodes_names = [x.knob('name').value() for x in parented_nodes]
            nodes_to_delete_str = ftrack_object.knob(
                asset_const.ASSET_LINK
            ).value()
            nodes_to_delete = nodes_to_delete_str.split(";")
            nodes_to_delete = set(nodes_to_delete + parented_nodes_names)
            for node_s in nodes_to_delete:
                node = nuke.toNode(node_s)
                self.logger.info("removing : {}".format(node.Class()))
                nuke.delete(node)

        nuke.delete(ftrack_object)

        return []


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = RemoveAssetNukePlugin(api_object)
    plugin.register()
