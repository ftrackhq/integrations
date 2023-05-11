# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from framework_core import plugin
from framework_nuke.plugin import NukeBasePlugin


class NukeAssetManagerActionPlugin(
    plugin.AssetManagerActionPlugin, NukeBasePlugin
):
    '''
    Class representing a Asset Manager Action Nuke Plugin
    '''
