# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_houdini.plugin import HoudiniBasePlugin


class AssetManagerDiscoverHoudiniPlugin(
    plugin.AssetManagerDiscoverPlugin, HoudiniBasePlugin
):
    '''
    Class representing a Asset Manager Discover Houdini Plugin
    '''
