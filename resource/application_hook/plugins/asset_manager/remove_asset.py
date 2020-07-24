# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import maya.cmds as cmd
import ftrack_api
from ftrack_connect_pipeline_maya import plugin
from ftrack_connect_pipeline_maya.constants import asset as asset_const
from ftrack_connect_pipeline_maya.utils import custom_commands as maya_utils


class RemoveAssetMayaPlugin(plugin.AssetManagerMenuActionMayaPlugin):
    plugin_name = 'remove_asset'

    def run(self, context=None, data=None, options=None):
        ftrack_asset_class = data

        referenceNode = False
        for node in cmd.listConnections(
                '{}.{}'.format(
                    ftrack_asset_class.ftrack_object, asset_const.ASSET_LINK
                )
        ):
            if cmd.nodeType(node) == 'reference':
                referenceNode = maya_utils.getReferenceNode(node)
                if referenceNode:
                    break

        if referenceNode:
            self.logger.debug("Removing reference: {}".format(referenceNode))
            maya_utils.remove_reference_node(referenceNode)
        else:
            nodes = cmd.listConnections(
                '{}.{}'.format(
                    ftrack_asset_class.ftrack_object, asset_const.ASSET_LINK
                )
            )
            for node in nodes:
                try:
                    self.logger.debug(
                        "Removing object: {}".format(node)
                    )
                    if cmd.objExists(node):
                        cmd.delete(node)
                except Exception as error:
                    self.logger.error(
                        'Node: {0} could not be deleted, error: {1}'.format(
                            node, error
                        )
                    )
        if cmd.objExists(ftrack_asset_class.ftrack_object):
            cmd.delete(ftrack_asset_class.ftrack_object)

        return []


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = RemoveAssetMayaPlugin(api_object)
    plugin.register()
