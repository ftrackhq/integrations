# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline.host.engine import AssetManagerEngine
from ftrack_connect_pipeline_3dsmax.asset import FtrackAssetNode


class MaxAssetManagerEngine(AssetManagerEngine):
    ftrack_asset_class = FtrackAssetNode
