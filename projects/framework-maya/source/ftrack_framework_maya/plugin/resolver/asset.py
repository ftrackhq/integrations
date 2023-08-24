# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_core import plugin
from ftrack_framework_maya.plugin import MayaBasePlugin


class MayaAssetResolverPlugin(plugin.AssetResolverPlugin, MayaBasePlugin):
    '''
    Class representing a Maya Asset Resolver Plugin
    '''
