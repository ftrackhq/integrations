# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import time
import nuke
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.host.engine import AssetManagerEngine
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo
from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils
from ftrack_connect_pipeline_nuke.constants import asset as asset_const
from ftrack_connect_pipeline_nuke.asset import NukeFtrackObjectManager
from ftrack_connect_pipeline_nuke.asset.dcc_object import NukeDccObject


class NukeAssetManagerEngine(AssetManagerEngine):
    engine_type = 'asset_manager'

    FtrackObjectManager = NukeFtrackObjectManager
    '''FtrackObjectManager class to use'''
    DccObject = NukeDccObject
    '''DccObject class to use'''

    def __init__(
        self, event_manager, host_types, host_id, asset_type_name=None
    ):
        '''Initialise AssetManagerEngine with *event_manager*, *host*, *hostid*
        and *asset_type_name*'''
        super(NukeAssetManagerEngine, self).__init__(
            event_manager, host_types, host_id, asset_type_name=asset_type_name
        )

    @nuke_utils.run_in_main_thread
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
            'message': message,
        }

        ftrack_asset_node_names = [
            node.name() for node in nuke_utils.get_nodes_with_ftrack_tab()
        ]
        ftrack_asset_info_list = []

        if ftrack_asset_node_names:
            for node_name in ftrack_asset_node_names:
                param_dict = self.DccObject.dictionary_from_object(node_name)
                # avoid read and write nodes containing the old ftrack tab
                # without information
                if not param_dict:
                    continue
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

    @nuke_utils.run_in_main_thread
    def unload_asset(self, asset_info, options=None, plugin=None):
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
            'method': 'unload_asset',
            'status': status,
            'result': result,
            'execution_time': 0,
            'message': message,
        }

        self.asset_info = asset_info
        dcc_object = self.DccObject(
            from_id=asset_info[asset_const.ASSET_INFO_ID]
        )
        self.dcc_object = dcc_object

        ftrack_node = nuke.toNode(self.dcc_object.name)
        if not ftrack_node:
            message = "There is no ftrack object"
            self.logger.debug(message)
            status = constants.UNKNOWN_STATUS

            end_time = time.time()
            total_time = end_time - start_time

            result_data['status'] = status
            result_data['result'] = result
            result_data['execution_time'] = total_time
            result_data['message'] = message

            self._notify_client(plugin, result_data)
            return status, result

        if ftrack_node.Class() == 'BackdropNode':
            parented_nodes = ftrack_node.getNodes()
            parented_nodes_names = [
                x.knob('name').value() for x in parented_nodes
            ]
            nodes_to_delete_str = ftrack_node.knob(
                asset_const.ASSET_LINK
            ).value()
            nodes_to_delete = nodes_to_delete_str.split(";")
            nodes_to_delete = set(nodes_to_delete + parented_nodes_names)
            for node_s in nodes_to_delete:
                node_to_delete = nuke.toNode(node_s)
                self.logger.debug(
                    "removing : {}".format(node_to_delete.Class())
                )
                try:
                    nuke.delete(node_to_delete)
                    result.append(str(node_s))
                    status = constants.SUCCESS_STATUS
                except Exception as error:
                    message = str(
                        'Could not delete the node {}, error: {}'.format(
                            str(node_s), error
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

        self.ftrack_object_manager.objects_loaded = False

        end_time = time.time()
        total_time = end_time - start_time

        result_data['status'] = status
        result_data['result'] = result
        result_data['execution_time'] = total_time

        self._notify_client(plugin, result_data)

        return status, result

    @nuke_utils.run_in_main_thread
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
            'message': message,
        }

        self.asset_info = asset_info
        dcc_object = self.DccObject(
            from_id=asset_info[asset_const.ASSET_INFO_ID]
        )
        self.dcc_object = dcc_object

        ftrack_node = nuke.toNode(self.dcc_object.name)
        if not ftrack_node:
            message = "There is no ftrack object"
            self.logger.debug(message)
            status = constants.UNKNOWN_STATUS

            end_time = time.time()
            total_time = end_time - start_time

            result_data['status'] = status
            result_data['result'] = result
            result_data['execution_time'] = total_time
            result_data['message'] = message

            self._notify_client(plugin, result_data)
            return status, result

        if ftrack_node.Class() == 'BackdropNode':
            parented_nodes = ftrack_node.getNodes()
            parented_nodes_names = [
                x.knob('name').value() for x in parented_nodes
            ]
            nodes_to_delete_str = ftrack_node.knob(
                asset_const.ASSET_LINK
            ).value()
            nodes_to_delete = nodes_to_delete_str.split(";")
            nodes_to_delete = set(nodes_to_delete + parented_nodes_names)
            for node_s in nodes_to_delete:
                node_to_delete = nuke.toNode(node_s)
                self.logger.debug(
                    "removing : {}".format(node_to_delete.Class())
                )
                try:
                    nuke.delete(node_to_delete)
                    result.append(str(node_s))
                    status = constants.SUCCESS_STATUS
                except Exception as error:
                    message = str(
                        'Could not delete the node {}, error: {}'.format(
                            str(node_s), error
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

        try:
            str_node = str(self.dcc_object.name)
            self.logger.debug("removing : {}".format(str_node))
            nuke.delete(ftrack_node)
            result.append(str_node)
            status = constants.SUCCESS_STATUS
        except Exception as error:
            message = str(
                'Could not delete the nuke dcc object, error: {}'.format(error)
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

    @nuke_utils.run_in_main_thread
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
            'message': message,
        }

        self.asset_info = asset_info
        dcc_object = self.DccObject(
            from_id=asset_info[asset_const.ASSET_INFO_ID]
        )
        self.dcc_object = dcc_object

        if options.get('clear_selection'):
            nuke_utils.cleanSelection()

        ftrack_node = nuke.toNode(self.dcc_object.name)

        parented_nodes = ftrack_node.getNodes()
        parented_nodes_names = [x.knob('name').value() for x in parented_nodes]
        nodes_to_select_str = ftrack_node.knob(asset_const.ASSET_LINK).value()
        nodes_to_select = (
            nodes_to_select_str.split(";")
            if len(nodes_to_select_str) > 0
            else []
        )
        nodes_to_select = set(nodes_to_select + parented_nodes_names)

        for node_s in nodes_to_select:
            try:
                node_to_select = nuke.toNode(node_s)
                node_to_select['selected'].setValue(True)
                result.append(str(node_s))
                status = constants.SUCCESS_STATUS
            except Exception as error:
                message = str(
                    'Could not select the node {}, error: {}'.format(
                        str(node_s), error
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

        try:
            ftrack_node['selected'].setValue(True)
            result.append(str(ftrack_node))
            status = constants.SUCCESS_STATUS
        except Exception as error:
            message = str(
                'Could not select the dcc_object, error: {}'.format(error)
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

    @nuke_utils.run_in_main_thread
    def select_assets(self, assets, options=None, plugin=None):
        '''
        Returns status dictionary and results dictionary keyed by the id for
        executing the :meth:`select_asset` for all the
        :class:`~ftrack_connect_pipeline.asset.FtrackAssetInfo` in the given
        *assets* list.

        *assets*: List of :class:`~ftrack_connect_pipeline.asset.FtrackAssetInfo`
        '''
        return super(NukeAssetManagerEngine, self).select_assets(
            assets=assets, options=options, plugin=plugin
        )
