# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_houdini.plugin import BaseHoudiniPlugin
from ftrack_connect_pipeline_houdini.asset import FtrackAssetTab


class AssetManagerActionHoudiniPlugin(
    plugin.AssetManagerActionPlugin, BaseHoudiniPlugin
):
    '''
    Class representing a Asset Manager Action Houdini Plugin
    '''
    ftrack_asset_class = FtrackAssetTab