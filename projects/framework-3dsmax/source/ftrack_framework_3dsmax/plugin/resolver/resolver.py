# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_framework_core import plugin
from ftrack_framework_3dsmax.plugin import MaxBasePlugin


class MaxResolverPlugin(plugin.ResolverPlugin, MaxBasePlugin):
    '''
    Class representing a 3DSMax Asset Resolver Plugin
    '''
