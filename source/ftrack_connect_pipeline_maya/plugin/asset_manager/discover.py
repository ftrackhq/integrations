# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_maya.plugin import MayaBasePlugin


class MayaAssetManagerDiscoverPlugin(
    plugin.AssetManagerDiscoverPlugin, MayaBasePlugin
):
    '''
    Class representing a Asset Manager Discover Maya Plugin
    '''
