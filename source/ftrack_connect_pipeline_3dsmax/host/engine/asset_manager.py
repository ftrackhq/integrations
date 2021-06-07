# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import time
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.host.engine import AssetManagerEngine
from ftrack_connect_pipeline_3dsmax.asset import FtrackAssetNode
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo
from ftrack_connect_pipeline_3dsmax.utils import custom_commands as max_utils
from ftrack_connect_pipeline_3dsmax.constants import asset as asset_const


class MaxAssetManagerEngine(AssetManagerEngine):
    ftrack_asset_class = FtrackAssetNode
    engine_type = 'asset_manager'

    def __init__(self, event_manager, host_types, host_id, asset_type_name=None):
        '''Initialise AssetManagerEngine with *event_manager*, *host*, *hostid*
        and *asset_type_name*'''
        super(MaxAssetManagerEngine, self).__init__(
            event_manager, host_types, host_id, asset_type_name=asset_type_name
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
            'plugin_type': constants.PLUGIN_AM_ACTION_TYPE,
            'method': 'discover_assets',
            'status': status,
            'result': result,
            'execution_time': 0,
            'message': message
        }

        ftrack_asset_nodes = max_utils.get_ftrack_helpers()
        ftrack_asset_info_list = []

        if ftrack_asset_nodes:
            for ftrack_object in ftrack_asset_nodes:
                obj = ftrack_object
                param_dict = FtrackAssetNode.get_parameters_dictionary(
                    obj
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

        plugin_type = constants.PLUGIN_AM_ACTION_TYPE
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

        deleted_nodes = []

        ftrack_asset_object = self.get_ftrack_asset_object(asset_info)

        try:
            # TODO: check if I have to get the object or not needed
            # ftrack_object = ftrack_asset_object.ftrack_object.Object
            deleted_nodes = max_utils.delete_all_children(ftrack_asset_object.ftrack_object)
            status = constants.SUCCESS_STATUS
        except Exception as error:
            message = 'Could not delete nodes, error: {}'.format(error)
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

        try:
            max_utils.delete_node(ftrack_asset_object.ftrack_object)
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
        deleted_nodes.append(ftrack_asset_object.ftrack_object)
        result = deleted_nodes

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

        plugin_type = constants.PLUGIN_AM_ACTION_TYPE
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

        selected_nodes=[]

        ftrack_asset_object = self.get_ftrack_asset_object(asset_info)

        if options.get('clear_selection'):
            max_utils.deselect_all()

        #max_utils.deselect_all()
        try:
            # TODO: check if I have to get the object or not needed
            # ftrack_object = ftrack_asset_class.ftrack_object.Object
            selected_nodes = max_utils.add_all_children_to_selection(
                ftrack_asset_object.ftrack_object
            )
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

        result = selected_nodes

        end_time = time.time()
        total_time = end_time - start_time

        result_data['status'] = status
        result_data['result'] = result
        result_data['execution_time'] = total_time

        self._notify_client(plugin, result_data)
        return status, result