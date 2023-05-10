# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from framework_core import plugin
from framework_maya.plugin import MayaBasePlugin


class MayaAssetManagerActionPlugin(
    plugin.AssetManagerActionPlugin, MayaBasePlugin
):
    '''
    Class representing a Asset Manager Action Maya Plugin
    '''
