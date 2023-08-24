# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_core import plugin
from ftrack_framework_nuke.plugin import NukeBasePlugin


class NukeAssetManagerActionPlugin(
    plugin.AssetManagerActionPlugin, NukeBasePlugin
):
    '''
    Class representing a Asset Manager Action Nuke Plugin
    '''
