# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_core import plugin
from ftrack_framework_3dsmax.plugin import MaxBasePlugin


class MaxAssetManagerActionPlugin(
    plugin.AssetManagerActionPlugin, MaxBasePlugin
):
    '''
    Class representing a Asset Manager Action Max Plugin
    '''
