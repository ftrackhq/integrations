# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

from framework_core import plugin
from framework_houdini.plugin import HoudiniBasePlugin


class AssetManagerActionHoudiniPlugin(
    plugin.AssetManagerActionPlugin, HoudiniBasePlugin
):
    '''
    Class representing a Asset Manager Action Houdini Plugin
    '''
