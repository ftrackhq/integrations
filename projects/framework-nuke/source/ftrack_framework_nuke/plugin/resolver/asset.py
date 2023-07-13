# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_framework_core import plugin
from ftrack_framework_nuke.plugin import NukeBasePlugin


class NukeAssetResolverPlugin(plugin.AssetResolverPlugin, NukeBasePlugin):
    '''
    Class representing a Resolver Nuke Plugin
    '''
