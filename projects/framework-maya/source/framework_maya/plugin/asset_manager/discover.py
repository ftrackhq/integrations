# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from framework_core import plugin
from framework_maya.plugin import MayaBasePlugin


class MayaAssetManagerDiscoverPlugin(
    plugin.AssetManagerDiscoverPlugin, MayaBasePlugin
):
    '''
    Class representing a Asset Manager Discover Maya Plugin
    '''
