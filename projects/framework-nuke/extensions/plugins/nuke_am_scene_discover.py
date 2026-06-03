# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_asset_manager.asset.ftrack_asset_info import (
    FtrackAssetInfo,
)
from ftrack_framework_nuke import utils as nuke_utils
from ftrack_framework_nuke.asset.dcc_object import NukeDccObject


class NukeAmSceneDiscoverPlugin(BasePlugin):
    """Walk the Nuke scene for ftrack-tagged Backdrops, reconstruct an
    FtrackAssetInfo from each one's knobs, and write the list to
    ``store['versions']`` so the Asset Manager dialog can render them.

    Mirrors the legacy ``NukeAssetManagerEngine.discover_assets()`` from
    ftrack-connect-pipeline-nuke, exposed as a framework plugin so it
    fits the current plugin-driven AM tool config chain.
    """

    name = "nuke.am_scene_discover"

    @nuke_utils.run_in_main_thread
    def run(self, store):
        versions = []
        for node in nuke_utils.get_nodes_with_ftrack_tab():
            param_dict = NukeDccObject.dictionary_from_object(node.name())
            if not param_dict:
                continue
            versions.append(FtrackAssetInfo(param_dict))

        self.logger.info(
            "Scene discover found {} ftrack-tracked asset(s)".format(
                len(versions)
            )
        )
        # Last writer wins for store['versions']; this plugin runs after
        # am_default_resolver so the AM reflects what's actually in the
        # script.
        store["versions"] = versions
        return {"versions": versions}


def register(api_object, **kw):
    """Register plugin to framework"""
    # Auto-registration handled by framework plugin discovery
    pass
