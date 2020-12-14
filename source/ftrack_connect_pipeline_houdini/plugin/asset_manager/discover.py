# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_houdini.plugin import BaseHoudiniPlugin
from ftrack_connect_pipeline_houdini.asset import FtrackAssetTab


class AssetManagerDiscoverHoudiniPlugin(
    plugin.AssetManagerDiscoverPlugin, BaseHoudiniPlugin
):
    '''
    Class representing a Asset Manager Discover Houdini Plugin
    '''
    ftrack_asset_class = FtrackAssetTab