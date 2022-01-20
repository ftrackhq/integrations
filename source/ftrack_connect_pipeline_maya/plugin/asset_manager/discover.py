# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_maya.plugin import BaseMayaPlugin
from ftrack_connect_pipeline_maya.asset import FtrackAssetNode


class AssetManagerDiscoverMayaPlugin(plugin.AssetManagerDiscoverPlugin, BaseMayaPlugin):
    '''
    Class representing a Asset Manager Discover Maya Plugin
    '''

    ftrack_asset_class = FtrackAssetNode
