# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import time
import hou
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.host.engine import AssetManagerEngine
from ftrack_connect_pipeline_houdini.asset import FtrackAssetTab
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo
from ftrack_connect_pipeline_houdini.utils import custom_commands as houdini_utils
from ftrack_connect_pipeline_houdini.constants import asset as asset_const


class HoudiniAssetManagerEngine(AssetManagerEngine):
    ftrack_asset_class = FtrackAssetTab
    engine_type = 'asset_manager'

    def __init__(self, event_manager, host_types, host_id, asset_type=None):
        '''Initialise AssetManagerEngine with *event_manager*, *host*, *hostid*
        and *asset_type*'''
        super(HoudiniAssetManagerEngine, self).__init__(
            event_manager, host_types, host_id, asset_type=asset_type
        )

    def discover_assets(self, assets=None, options=None, plugin=None):
        '''
        Discover all the assets in the scene:
        Returns status and result
        '''
        try:
            start_time = time.time()
            status = constants.UNKNOWN_STATUS
            result = []
            message = None

            result_data = {
                'plugin_name': 'discover_assets',
                'plugin_type': 'action',
                'status': status,
                'result': result,
                'execution_time': 0,
                'message': message
            }

            ftrack_asset_nodes = houdini_utils.get_ftrack_objects()
            ftrack_asset_info_list = []

            for obj in ftrack_asset_nodes:
                param_dict = FtrackAssetTab.get_parameters_dictionary(
                    obj
                )
                # avoid objects containing the old ftrack tab without information
                if not param_dict:
                    continue
                node_asset_info = FtrackAssetInfo(param_dict)
                ftrack_asset_info_list.append(node_asset_info)

            if not ftrack_asset_info_list:
                status = constants.ERROR_STATUS
            else:
                status = constants.SUCCESS_STATUS
            result = ftrack_asset_info_list

            end_time = time.time()
            total_time = end_time - start_time

            result_data['status'] = status
            result_data['result'] = result
            result_data['execution_time'] = total_time

            self._notify_client(plugin, result_data)

        except:
            import traceback
            self.logger.error(traceback.format_exc())
            raise

        return status, result

    def remove_asset(self, asset_info, options=None, plugin=None):
        '''
        Removes the given *asset_info* from the scene.
        Returns status and result
        '''
        try:
            start_time = time.time()
            status = constants.UNKNOWN_STATUS
            result = []
            message = None

            result_data = {
                'plugin_name': 'remove_asset',
                'plugin_type': 'action',
                'status': status,
                'result': result,
                'execution_time': 0,
                'message': message
            }

            try:
                obj_path = FtrackAssetTab.get_ftrack_object_path_from_scene_on_asset_info(asset_info)
                if not obj_path:
                    message = "There is no ftrack object in the current scene @ path '{}'".format(obj_path)
                    self.logger.warning(message)
                    status = constants.UNKNOWN_STATUS
                else:
                    obj = hou.node(obj_path)
                    try:
                        str_node = obj_path
                        obj.destroy()
                        result.append(str_node)
                        status = constants.SUCCESS_STATUS
                    except Exception as error:
                        message = str(
                            'Could not delete the ftrack_object, error: {}'.format(error)
                        )
                        self.logger.error(message)
                        status = constants.ERROR_STATUS
                    else:
                        bool_status = constants.status_bool_mapping[status]
                        if not bool_status:
                            status = constants.UNKNOWN_STATUS
            finally:
                end_time = time.time()
                total_time = end_time - start_time

                result_data['status'] = status
                result_data['result'] = result
                result_data['execution_time'] = total_time

            self._notify_client(plugin, result_data)
        except:
            import traceback
            self.logger.error(traceback.format_exc())
            raise
        return status, result

    def select_asset(self, asset_info, options=None, plugin=None):
        '''
        Selects the given *asset_info* from the scene.
        *options* can contain clear_selection to clear the selection before
        select the given *asset_info*.
        Returns status and result
        '''
        try:

            start_time = time.time()
            status = constants.UNKNOWN_STATUS
            result = []
            message = None

            result_data = {
                'plugin_name': 'select_asset',
                'plugin_type': 'action',
                'status': status,
                'result': result,
                'execution_time': 0,
                'message': message
            }
            try:
                obj_path = FtrackAssetTab.get_ftrack_object_path_from_scene_on_asset_info(asset_info)
                if not obj_path:
                    message = "There is no ftrack object in the current scene @ path '{}'".format(obj_path)
                    self.logger.warning(message)
                    status = constants.UNKNOWN_STATUS
                else:
                    obj = hou.node(obj_path)
                    try:
                        str_node = obj_path
                        hou.Node.setSelected(obj, True, clear_all_selected=(options.get('clear_selection') is True))
                        result.append(str_node)
                        status = constants.SUCCESS_STATUS
                    except Exception as error:
                        message = str(
                            'Could not delete the ftrack_object, error: {}'.format(error)
                        )
                        self.logger.error(message)
                        status = constants.ERROR_STATUS
                    else:
                        bool_status = constants.status_bool_mapping[status]
                        if not bool_status:
                            status = constants.UNKNOWN_STATUS
            finally:
                end_time = time.time()
                total_time = end_time - start_time

                result_data['status'] = status
                result_data['result'] = result
                result_data['execution_time'] = total_time

            self._notify_client(plugin, result_data)

        except:
            import traceback
            self.logger.error(traceback.format_exc())
            raise

        return status, result
