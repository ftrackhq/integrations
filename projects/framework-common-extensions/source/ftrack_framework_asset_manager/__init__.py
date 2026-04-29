# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

"""Asset Manager module for the ftrack pipeline framework.

Provides asset tracking, management, and version control functionality
for DCC applications integrated with ftrack.
"""

__version__ = '1.0.0'

from ftrack_framework_asset_manager.asset.constants import *  # noqa: F401,F403
from ftrack_framework_asset_manager.asset.ftrack_asset_info import (
    FtrackAssetInfo,
)
from ftrack_framework_asset_manager.asset.dcc_object import DccObject
from ftrack_framework_asset_manager.asset.ftrack_object_manager import (
    FtrackObjectManager,
)
from ftrack_framework_asset_manager.asset.asset_list_model import (
    AssetListModel,
)
