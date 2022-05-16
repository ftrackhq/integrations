# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_nuke.plugin import NukeBasePlugin


class NukeAssetManagerActionPlugin(
    plugin.AssetManagerActionPlugin, NukeBasePlugin
):
    '''
    Class representing a Asset Manager Action Nuke Plugin
    '''
