# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import nuke

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_asset_manager.asset import constants as asset_const
from ftrack_framework_nuke import utils as nuke_utils
from ftrack_framework_nuke.asset import constants as nuke_asset_const
from ftrack_framework_nuke.asset.dcc_object import NukeDccObject


class NukeAmUnloadAssetsPlugin(BasePlugin):
    """Delete the parented content nodes of each Backdrop in
    ``self.options['assets']`` while keeping the Backdrop tracking node
    itself. Flips the Backdrop's ``objects_loaded`` knob to ``False``.
    """

    name = "nuke.am_unload_assets"

    @nuke_utils.run_in_main_thread
    def run(self, store):
        assets = self.options.get("assets") or []
        if not assets:
            self.logger.debug("nuke.am_unload_assets: no assets in options")
            return

        unloaded_count = 0

        for asset_info in assets:
            asset_info_id = asset_info.get(asset_const.ASSET_INFO_ID)
            if not asset_info_id:
                continue

            dcc_object = NukeDccObject(from_id=asset_info_id)
            if not dcc_object.name:
                self.logger.warning(
                    "nuke.am_unload_assets: no Backdrop found for "
                    "asset_info_id={}".format(asset_info_id)
                )
                continue

            ftrack_node = nuke.toNode(dcc_object.name)
            if ftrack_node is None:
                continue

            node_names_to_delete = set()
            for n in ftrack_node.getNodes() or []:
                node_names_to_delete.add(n.knob("name").value())
            link_value = ftrack_node.knob(nuke_asset_const.ASSET_LINK).value()
            if link_value:
                node_names_to_delete.update(
                    n for n in link_value.split(";") if n
                )

            for node_name in node_names_to_delete:
                node = nuke.toNode(node_name)
                if node is None:
                    continue
                try:
                    nuke.delete(node)
                except Exception as error:
                    self.logger.error(
                        "nuke.am_unload_assets: could not delete {}: {}".format(
                            node_name, error
                        )
                    )

            ftrack_node.knob(nuke_asset_const.ASSET_LINK).setValue("")
            loaded_knob = ftrack_node.knob(asset_const.OBJECTS_LOADED)
            if loaded_knob is not None:
                loaded_knob.setValue("False")
            unloaded_count += 1

        self.logger.info(
            "nuke.am_unload_assets: unloaded {} asset(s)".format(
                unloaded_count
            )
        )


def register(api_object, **kw):
    """Register plugin to framework"""
    pass
