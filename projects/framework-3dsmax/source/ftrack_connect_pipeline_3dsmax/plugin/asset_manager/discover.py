# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_3dsmax.plugin import MaxBasePlugin


class MaxAssetManagerDiscoverPlugin(
    plugin.AssetManagerDiscoverPlugin, MaxBasePlugin
):
    '''
    Class representing a Asset Manager Discover Max Plugin
    '''
