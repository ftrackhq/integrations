# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline.host.engine import AssetManagerEngine
from ftrack_connect_pipeline_maya.asset import FtrackAssetNode


class MayaAssetManagerEngine(AssetManagerEngine):
    ftrack_asset_class = FtrackAssetNode
