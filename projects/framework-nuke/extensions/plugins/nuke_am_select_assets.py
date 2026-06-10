# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import nuke

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_asset_manager.asset import constants as asset_const
from ftrack_framework_nuke import utils as nuke_utils
from ftrack_framework_nuke.asset import constants as nuke_asset_const
from ftrack_framework_nuke.asset.dcc_object import NukeDccObject


class NukeAmSelectAssetsPlugin(BasePlugin):
    """Select the scene nodes for each ftrack-tracked asset in
    ``self.options['assets']``.

    For each asset_info, find the Backdrop tagged with its
    ``asset_info_id``, select the Backdrop, all nodes it contains, and any
    nodes listed in its ``asset_link`` knob. The first asset clears the
    existing selection; subsequent assets add to it.
    """

    name = "nuke.am_select_assets"

    @nuke_utils.run_in_main_thread
    def run(self, store):
        assets = self.options.get("assets") or []
        if not assets:
            self.logger.debug("nuke.am_select_assets: no assets in options")
            return

        nuke_utils.clean_selection()
        selected_names = []

        for asset_info in assets:
            asset_info_id = asset_info.get(asset_const.ASSET_INFO_ID)
            if not asset_info_id:
                self.logger.warning(
                    "nuke.am_select_assets: missing asset_info_id; skipping"
                )
                continue

            dcc_object = NukeDccObject(from_id=asset_info_id)
            if not dcc_object.name:
                self.logger.warning(
                    "nuke.am_select_assets: no Backdrop found for "
                    "asset_info_id={}".format(asset_info_id)
                )
                continue

            ftrack_node = nuke.toNode(dcc_object.name)
            if ftrack_node is None:
                continue

            node_names = set()
            for n in ftrack_node.getNodes() or []:
                node_names.add(n.knob("name").value())
            link_value = ftrack_node.knob(nuke_asset_const.ASSET_LINK).value()
            if link_value:
                node_names.update(n for n in link_value.split(";") if n)

            for node_name in node_names:
                node = nuke.toNode(node_name)
                if node is None:
                    continue
                sel_knob = node.knob("selected")
                if sel_knob is not None:
                    sel_knob.setValue(True)
                    selected_names.append(node_name)

            ftrack_node["selected"].setValue(True)
            selected_names.append(ftrack_node.name())

        self.logger.info(
            "nuke.am_select_assets: selected {} node(s) across {} asset(s)".format(
                len(selected_names), len(assets)
            )
        )


def register(api_object, **kw):
    """Register plugin to framework"""
    pass
