# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_nuke.plugin import (
    BaseNukePlugin, BaseNukePluginWidget
)

from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils
from ftrack_connect_pipeline_nuke.utils import ftrack_asset_node
from ftrack_connect_pipeline_nuke import constants

class LoaderImporterNukePlugin(plugin.LoaderImporterPlugin, BaseNukePlugin):
    ''' Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''
    asset_node_type = ftrack_asset_node.FtrackAssetNode



class ImporterNukeWidget(pluginWidget.LoaderImporterWidget, BaseNukePluginWidget):
    ''' Class representing a Collector Widget

    .. note::

        _required_output a List
    '''

