# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from framework_core import plugin
from framework_houdini.plugin import HoudiniBasePlugin


class AssetManagerDiscoverHoudiniPlugin(
    plugin.AssetManagerDiscoverPlugin, HoudiniBasePlugin
):
    '''
    Class representing a Asset Manager Discover Houdini Plugin
    '''
