# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

"""
Ftrack Framework Asset Manager Package

This package provides the foundation layer for asset management in ftrack's
refactored monorepo architecture.
"""

from .asset import *
from .asset.constants import VERSION as __version__

# Convenience imports for common usage
from .asset.ftrack_asset_info import FtrackAssetInfo
from .asset.dcc_object import DccObject
from .asset.ftrack_object_manager import FtrackObjectManager
