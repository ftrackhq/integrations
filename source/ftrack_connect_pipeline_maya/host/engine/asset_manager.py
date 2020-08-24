# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import maya.cmds as cmd

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.host.engine import AssetManagerEngine
from ftrack_connect_pipeline_maya.asset import FtrackAssetNode
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo
from ftrack_connect_pipeline_maya.utils import custom_commands as maya_utils
from ftrack_connect_pipeline_maya.constants import asset as asset_const


class MayaAssetManagerEngine(AssetManagerEngine):
    ftrack_asset_class = FtrackAssetNode
    engine_type = 'asset_manager'

    def __init__(self, event_manager, host, hostid, asset_type=None):
        '''Initialise AssetManagerEngine with *event_manager*, *host*, *hostid*
        and *asset_type*'''
        super(MayaAssetManagerEngine, self).__init__(
            event_manager, host, hostid, asset_type=asset_type
        )

    def discover_assets(self, plugin, assets, args):
        status = constants.UNKNOWN_STATUS
        ftrack_asset_nodes = maya_utils.get_ftrack_nodes()
        ftrack_asset_info_list = []

        for ftrack_object in ftrack_asset_nodes:
            param_dict = FtrackAssetNode.get_parameters_dictionary(
                ftrack_object
            )
            node_asset_info = FtrackAssetInfo(param_dict)
            ftrack_asset_info_list.append(node_asset_info)

        # ftrack_asset_list = []
        #
        # for asset_info in ftrack_asset_info_list:
        #     ftrack_asset_class = FtrackAssetNode(self.event_manager)
        #     ftrack_asset_class.asset_info = asset_info
        #     ftrack_asset_class.init_ftrack_object()
        #     ftrack_asset_list.append(ftrack_asset_class)

        #return ftrack_asset_info_list
        if not ftrack_asset_info_list:
            status = constants.ERROR_STATUS
        else:
            status = constants.SUCCESS_STATUS
        result = ftrack_asset_info_list

        return status, result

    def remove_asset(self, ftrack_asset_object):

        referenceNode = False
        for node in cmd.listConnections(
                '{}.{}'.format(
                    ftrack_asset_object.ftrack_object, asset_const.ASSET_LINK
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
                    ftrack_asset_object.ftrack_object, asset_const.ASSET_LINK
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
        if cmd.objExists(ftrack_asset_object.ftrack_object):
            cmd.delete(ftrack_asset_object.ftrack_object)

        return True
