# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_nuke.plugin import BaseNukePlugin
from ftrack_connect_pipeline_nuke.asset import FtrackAssetTab


class AssetManagerActionNukePlugin(
    plugin.AssetManagerActionPlugin, BaseNukePlugin
):
    ''' Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''
    ftrack_asset_class = FtrackAssetTab