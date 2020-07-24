# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import maya.cmds as cmd
import ftrack_api
from ftrack_connect_pipeline_maya import plugin
from ftrack_connect_pipeline_maya.constants import asset as asset_const


class SelectAssetMayaPlugin(plugin.AssetManagerMenuActionMayaPlugin):
    plugin_name = 'select_asset'

    def run(self, context=None, data=None, options=None):
        ftrack_asset_class = data
        if options.get('clear_selection'):
            cmd.select(cl=True)

        nodes = cmd.listConnections(
            '{}.{}'.format(
                ftrack_asset_class.ftrack_object, asset_const.ASSET_LINK
            )
        )
        for node in nodes:
            cmd.select(node, add=True)

        return []


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = SelectAssetMayaPlugin(api_object)
    plugin.register()
