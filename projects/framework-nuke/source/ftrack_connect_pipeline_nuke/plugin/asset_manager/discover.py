# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_nuke.plugin import NukeBasePlugin


class NukeAssetManagerDiscoverPlugin(
    plugin.AssetManagerDiscoverPlugin, NukeBasePlugin
):
    '''
    Class representing a Asset Manager Discover Nuke Plugin
    '''
