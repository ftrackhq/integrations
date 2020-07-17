# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline.host.engine import AssetManagerEngine
from ftrack_connect_pipeline_nuke.asset import FtrackAssetTab


class NukeAssetManagerEngine(AssetManagerEngine):
    ftrack_asset_class = FtrackAssetTab
