# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_core import plugin
from ftrack_framework_houdini.plugin import HoudiniBasePlugin


class AssetManagerActionHoudiniPlugin(
    plugin.AssetManagerActionPlugin, HoudiniBasePlugin
):
    '''
    Class representing a Asset Manager Action Houdini Plugin
    '''
