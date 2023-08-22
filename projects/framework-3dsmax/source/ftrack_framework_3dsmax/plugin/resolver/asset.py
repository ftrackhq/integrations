# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_core import plugin
from ftrack_framework_3dsmax.plugin import MaxBasePlugin


class MaxAssetResolverPlugin(plugin.AssetResolverPlugin, MaxBasePlugin):
    '''
    Class representing a 3DSMax Asset Resolver Plugin
    '''
