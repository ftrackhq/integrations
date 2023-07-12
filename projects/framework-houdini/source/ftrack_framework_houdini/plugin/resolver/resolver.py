# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_core import plugin
from ftrack_framework_houdini.plugin import HoudiniBasePlugin


class HoudiniResolverPlugin(plugin.ResolverPlugin, HoudiniBasePlugin):
    '''
    Class representing a Resolver Houdini Plugin
    '''
