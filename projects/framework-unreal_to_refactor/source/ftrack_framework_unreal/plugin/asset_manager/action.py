# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_core import plugin
from ftrack_framework_unreal.plugin import UnrealBasePlugin


class UnrealAssetManagerActionPlugin(
    plugin.AssetManagerActionPlugin, UnrealBasePlugin
):
    '''
    Class representing an Asset Manager Action Unreal Plugin
    '''
