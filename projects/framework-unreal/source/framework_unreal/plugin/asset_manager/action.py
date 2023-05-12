# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from framework_core import plugin
from framework_unreal.plugin import UnrealBasePlugin


class UnrealAssetManagerActionPlugin(
    plugin.AssetManagerActionPlugin, UnrealBasePlugin
):
    '''
    Class representing an Asset Manager Action Unreal Plugin
    '''
