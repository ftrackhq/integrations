# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_houdini.plugin import HoudiniBasePlugin


class AssetManagerActionHoudiniPlugin(
    plugin.AssetManagerActionPlugin, HoudiniBasePlugin
):
    '''
    Class representing a Asset Manager Action Houdini Plugin
    '''
