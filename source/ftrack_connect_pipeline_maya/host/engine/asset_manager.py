# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import time
import maya.cmds as cmds

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.host.engine import AssetManagerEngine
from ftrack_connect_pipeline_maya.asset import FtrackAssetNode
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo
from ftrack_connect_pipeline_maya.utils import custom_commands as maya_utils
from ftrack_connect_pipeline_maya.constants import asset as asset_const


class MayaAssetManagerEngine(AssetManagerEngine):
    ftrack_asset_class = FtrackAssetNode
    engine_type = 'asset_manager'

    def __init__(self, event_manager, host_types, host_id, asset_type=None):
        '''Initialise AssetManagerEngine with *event_manager*, *host*, *hostid*
        and *asset_type*'''
        super(MayaAssetManagerEngine, self).__init__(
            event_manager, host_types, host_id, asset_type=asset_type
        )

    def discover_assets(self, assets=None, options=None, plugin=None):
        '''
        Discover all the assets in the scene:
        Returns status and result
        '''
        start_time = time.time()
        status = constants.UNKNOWN_STATUS
        result = []
        message = None

        result_data = {
            'plugin_name': None,
            'plugin_type': None,
            'method': 'discover_assets',
            'status': status,
            'result': result,
            'execution_time': 0,
            'message': message
        }

        ftrack_asset_nodes = maya_utils.get_ftrack_nodes()
        ftrack_asset_info_list = []

        if ftrack_asset_nodes:
            for ftrack_object in ftrack_asset_nodes:
                param_dict = FtrackAssetNode.get_parameters_dictionary(
                    ftrack_object
                )
                node_asset_info = FtrackAssetInfo(param_dict)
                ftrack_asset_info_list.append(node_asset_info)

            if not ftrack_asset_info_list:
                status = constants.ERROR_STATUS
            else:
                status = constants.SUCCESS_STATUS
        else:
            self.logger.debug("No assets in the scene")
            status = constants.SUCCESS_STATUS

        result = ftrack_asset_info_list

        end_time = time.time()
        total_time = end_time - start_time

        result_data['status'] = status
        result_data['result'] = result
        result_data['execution_time'] = total_time

        self._notify_client(plugin, result_data)

        return status, result

    def remove_asset(self, asset_info, options=None, plugin=None):
        '''
        Removes the given *asset_info* from the scene.
        Returns status and result
        '''
        start_time = time.time()
        status = constants.UNKNOWN_STATUS
        result = []
        message = None

        plugin_type = None
        plugin_name = None
        if plugin:
            plugin_type = '{}.{}'.format('asset_manager', plugin['type'])
            plugin_name = plugin.get('name')

        result_data = {
            'plugin_name': plugin_name,
            'plugin_type': plugin_type,
            'method': 'remove_asset',
            'status': status,
            'result': result,
            'execution_time': 0,
            'message': message
        }

        ftrack_asset_object = self.get_ftrack_asset_object(asset_info)

        reference_node = False
        for node in cmds.listConnections(
            '{}.{}'.format(
                ftrack_asset_object.ftrack_object, asset_const.ASSET_LINK
            )
        ):
            if cmds.nodeType(node) == 'reference':
                reference_node = maya_utils.getReferenceNode(node)
                if reference_node:
                    break

        if reference_node:
            self.logger.debug("Removing reference: {}".format(reference_node))
            try:
                maya_utils.remove_reference_node(reference_node)
                result.append(str(reference_node))
                status = constants.SUCCESS_STATUS
            except Exception as error:
                message = str(
                    'Could not remove the reference node {}, error: {}'.format(
                        str(reference_node), error)
                )
                self.logger.error(message)
                status = constants.ERROR_STATUS

            bool_status = constants.status_bool_mapping[status]
            if not bool_status:
                end_time = time.time()
                total_time = end_time - start_time

                result_data['status'] = status
                result_data['result'] = result
                result_data['execution_time'] = total_time
                result_data['message'] = message

                self._notify_client(plugin, result_data)
                return status, result
        else:
            nodes = cmds.listConnections(
                '{}.{}'.format(
                    ftrack_asset_object.ftrack_object, asset_const.ASSET_LINK
                )
            )
            for node in nodes:
                self.logger.debug(
                    "Removing object: {}".format(node)
                )
                try:
                    if cmds.objExists(node):
                        cmds.delete(node)
                        result.append(str(node))
                        status = constants.SUCCESS_STATUS
                except Exception as error:
                    message = str(
                        'Node: {0} could not be deleted, error: {1}'.format(
                            node, error
                        )
                    )
                    self.logger.error(message)
                    status = constants.ERROR_STATUS

                bool_status = constants.status_bool_mapping[status]
                if not bool_status:
                    end_time = time.time()
                    total_time = end_time - start_time

                    result_data['status'] = status
                    result_data['result'] = result
                    result_data['execution_time'] = total_time
                    result_data['message'] = message

                    self._notify_client(plugin, result_data)
                    return status, result

        if cmds.objExists(ftrack_asset_object.ftrack_object):
            try:
                cmds.delete(ftrack_asset_object.ftrack_object)
                result.append(str(ftrack_asset_object.ftrack_object))
                status = constants.SUCCESS_STATUS
            except Exception as error:
                message = str(
                    'Could not delete the ftrack_object, error: {}'.format(error)
                )
                self.logger.error(message)
                status = constants.ERROR_STATUS

            bool_status = constants.status_bool_mapping[status]
            if not bool_status:
                end_time = time.time()
                total_time = end_time - start_time

                result_data['status'] = status
                result_data['result'] = result
                result_data['execution_time'] = total_time
                result_data['message'] = message

                self._notify_client(plugin, result_data)

                return status, result

        end_time = time.time()
        total_time = end_time - start_time

        result_data['status'] = status
        result_data['result'] = result
        result_data['execution_time'] = total_time

        self._notify_client(plugin, result_data)

        return status, result

    def select_asset(self, asset_info, options=None, plugin=None):
        '''
        Selects the given *asset_info* from the scene.
        *options* can contain clear_selection to clear the selection before
        select the given *asset_info*.
        Returns status and result
        '''
        start_time = time.time()
        status = constants.UNKNOWN_STATUS
        result = []
        message = None

        plugin_type = None
        plugin_name = None
        if plugin:
            plugin_type = '{}.{}'.format('asset_manager', plugin['type'])
            plugin_name = plugin.get('name')

        result_data = {
            'plugin_name': plugin_name,
            'plugin_type': plugin_type,
            'method': 'select_asset',
            'status': status,
            'result': result,
            'execution_time': 0,
            'message': message
        }

        ftrack_asset_object = self.get_ftrack_asset_object(asset_info)

        if options.get('clear_selection'):
            cmds.select(cl=True)

        nodes = cmds.listConnections(
            '{}.{}'.format(
                ftrack_asset_object.ftrack_object, asset_const.ASSET_LINK
            )
        )
        for node in nodes:
            try:
                cmds.select(node, add=True)
                result.append(str(node))
                status = constants.SUCCESS_STATUS
            except Exception as error:
                message = str(
                    'Could not select the node {}, error: {}'.format(
                        str(node), error)
                )
                self.logger.error(message)
                status = constants.ERROR_STATUS

            bool_status = constants.status_bool_mapping[status]
            if not bool_status:
                end_time = time.time()
                total_time = end_time - start_time

                result_data['status'] = status
                result_data['result'] = result
                result_data['execution_time'] = total_time
                result_data['message'] = message

                self._notify_client(plugin, result_data)
                return status, result

        end_time = time.time()
        total_time = end_time - start_time

        result_data['status'] = status
        result_data['result'] = result
        result_data['execution_time'] = total_time

        self._notify_client(plugin, result_data)

        return status, result