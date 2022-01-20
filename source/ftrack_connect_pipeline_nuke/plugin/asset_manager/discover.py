# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_nuke.plugin import BaseNukePlugin
from ftrack_connect_pipeline_nuke.asset import FtrackAssetTab


class AssetManagerDiscoverNukePlugin(plugin.AssetManagerDiscoverPlugin, BaseNukePlugin):
    '''
    Class representing a Asset Manager Discover Nuke Plugin
    '''

    ftrack_asset_class = FtrackAssetTab
