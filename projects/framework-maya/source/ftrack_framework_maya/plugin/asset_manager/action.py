# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_framework_core import plugin
from ftrack_framework_maya.plugin import MayaBasePlugin


class MayaAssetManagerActionPlugin(
    plugin.AssetManagerActionPlugin, MayaBasePlugin
):
    '''
    Class representing a Asset Manager Action Maya Plugin
    '''
