# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_harmony.plugin import HarmonyBasePlugin


class HarmonyAssetManagerActionPlugin(
    plugin.AssetManagerActionPlugin, HarmonyBasePlugin
):
    '''
    Class representing a Asset Manager Action Harmony Plugin
    '''
