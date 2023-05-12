# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from framework_core import plugin
from framework_3dsmax.plugin import MaxBasePlugin


class MaxAssetManagerDiscoverPlugin(
    plugin.AssetManagerDiscoverPlugin, MaxBasePlugin
):
    '''
    Class representing a Asset Manager Discover Max Plugin
    '''
