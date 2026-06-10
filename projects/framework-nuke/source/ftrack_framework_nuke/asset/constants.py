# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

# Re-export every base asset-manager constant so call sites that read
# ``asset_const.REFERENCE_OBJECT`` / ``asset_const.DEPENDENCY_IDS`` /
# ``asset_const.ASSET_INFO_ID`` against this module (NukeDccObject,
# NukeAssetManagerEngine) resolve, and ``KEYS`` matches the full set the
# manager-side ``_sync`` writes.
from ftrack_framework_asset_manager.asset.constants import *  # noqa: F401,F403

FTRACK_PLUGIN_ID = 2386071295
FTRACK_PLUGIN_TYPE = "ftracktab"
ASSET_LINK = "asset_link"
