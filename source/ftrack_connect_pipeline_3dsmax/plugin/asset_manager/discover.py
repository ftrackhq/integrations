# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_3dsmax.plugin import BaseMaxPlugin
from ftrack_connect_pipeline_3dsmax.asset import FtrackAssetNode


class AssetManagerDiscoverMaxPlugin(
    plugin.AssetManagerDiscoverPlugin, BaseMaxPlugin
):
    '''
    Class representing a Asset Manager Discover Max Plugin
    '''
    ftrack_asset_class = FtrackAssetNode