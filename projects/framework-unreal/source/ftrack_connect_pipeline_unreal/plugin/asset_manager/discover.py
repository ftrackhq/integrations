# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_unreal.plugin import UnrealBasePlugin


class UnrealAssetManagerDiscoverPlugin(
    plugin.AssetManagerDiscoverPlugin, UnrealBasePlugin
):
    '''
    Class representing an Asset Manager Discover Unreal Plugin
    '''
