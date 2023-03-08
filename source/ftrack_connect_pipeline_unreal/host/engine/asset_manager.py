# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import time
import random
import string
import os

import unreal

from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline.host.engine import AssetManagerEngine
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo

from ftrack_connect_pipeline_unreal import utils as unreal_utils
from ftrack_connect_pipeline_unreal.constants import asset as asset_const
from ftrack_connect_pipeline_unreal.asset import UnrealFtrackObjectManager
from ftrack_connect_pipeline_unreal.asset.dcc_object import UnrealDccObject


class UnrealAssetManagerEngine(AssetManagerEngine):
    engine_type = 'asset_manager'

    FtrackObjectManager = UnrealFtrackObjectManager
    '''FtrackObjectManager class to use'''
    DccObject = UnrealDccObject
    '''DccObject class to use'''

    def __init__(
        self, event_manager, host_types, host_id, asset_type_name=None
    ):
        '''Initialise AssetManagerEngine with *event_manager*, *host*, *hostid*
        and *asset_type_name*'''
        super(UnrealAssetManagerEngine, self).__init__(
            event_manager, host_types, host_id, asset_type_name=asset_type_name
        )

    @unreal_utils.run_in_main_thread
    def discover_assets(self, assets=None, options=None, plugin=None):
        '''
        Discover all the assets in the scene:
        Returns status and result
        '''
        start_time = time.time()
        status = core_constants.UNKNOWN_STATUS
        result = []
        message = None

        result_data = {
            'plugin_name': None,
            'plugin_type': core_constants.PLUGIN_AM_ACTION_TYPE,
            'method': 'discover_assets',
            'status': status,
            'result': result,
            'execution_time': 0,
            'message': message,
        }

        ftrack_asset_nodes = unreal_utils.get_ftrack_nodes()
        ftrack_asset_info_list = []

        if ftrack_asset_nodes:
            for node_name in ftrack_asset_nodes:
                param_dict = self.DccObject.dictionary_from_object(node_name)
                node_asset_info = FtrackAssetInfo(param_dict)
                ftrack_asset_info_list.append(node_asset_info)

            if not ftrack_asset_info_list:
                status = core_constants.ERROR_STATUS
            else:
                status = core_constants.SUCCESS_STATUS
        else:
            self.logger.debug("No assets in the project")
            status = core_constants.SUCCESS_STATUS

        result = ftrack_asset_info_list

        end_time = time.time()
        total_time = end_time - start_time

        result_data['status'] = status
        result_data['result'] = result
        result_data['execution_time'] = total_time

        self._notify_client(plugin, result_data)

        return status, result

    @unreal_utils.run_in_main_thread
    def select_asset(self, asset_info, options=None, plugin=None):
        '''
        Selects the given *asset_info* from the scene.
        *options* can contain clear_selection to clear the selection before
        select the given *asset_info*.
        Returns status and result
        '''
        start_time = time.time()
        status = core_constants.UNKNOWN_STATUS
        result = []
        message = None

        plugin_type = core_constants.PLUGIN_AM_ACTION_TYPE
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

        asset_paths = []
        try:
            asset_paths = unreal_utils.get_connected_nodes_from_dcc_object(
                dcc_object.name
            )
            if not asset_paths:
                raise Exception(
                    'No Unreal asset found for {}'.format(dcc_object.name)
                )
            unreal.EditorAssetLibrary.sync_browser_to_objects(asset_paths)
            status = core_constants.SUCCESS_STATUS
        except Exception as error:
            message = str(
                'Could not select the assets {}, error: {}'.format(
                    str(asset_paths), error
                )
            )
            self.logger.error(message)
            status = core_constants.ERROR_STATUS

        bool_status = core_constants.status_bool_mapping[status]
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

    @unreal_utils.run_in_main_thread
    def select_assets(self, assets, options=None, plugin=None):
        '''
        Returns status dictionary and results dictionary keyed by the id for
        executing the :meth:`select_asset` for all the
        :class:`~ftrack_connect_pipeline.asset.FtrackAssetInfo` in the given
        *assets* list.

        *assets*: List of :class:`~ftrack_connect_pipeline.asset.FtrackAssetInfo`
        '''
        return super(UnrealAssetManagerEngine, self).select_assets(
            assets=assets, options=options, plugin=plugin
        )

    @unreal_utils.run_in_main_thread
    def load_asset(self, asset_info, options=None, plugin=None):
        '''
        Override load_asset method to deal with unloaded assets.
        '''

        # It's an import, so load asset with the main method
        return super(UnrealAssetManagerEngine, self).load_asset(
            asset_info=asset_info, options=options, plugin=plugin
        )

    @unreal_utils.run_in_main_thread
    def change_version(self, asset_info, options, plugin=None):
        '''
        (Override) Support Unreal asset version change preserving in memory references.
        '''
        start_time = time.time()
        status = core_constants.UNKNOWN_STATUS
        result = {}
        message = None

        plugin_type = core_constants.PLUGIN_AM_ACTION_TYPE
        plugin_name = None
        if plugin:
            plugin_type = '{}.{}'.format('asset_manager', plugin['type'])
            plugin_name = plugin.get('name')

        result_data = {
            'plugin_name': plugin_name,
            'plugin_type': plugin_type,
            'method': 'change_version',
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

        nodes = (
                unreal_utils.get_connected_nodes_from_dcc_object(
                    self.dcc_object.name
                )
                or []
        )
        temporary_assets = {}
        # Rename
        for node in nodes:
            # Generate temp name and map it to class
            try:
                if unreal_utils.node_exists(node):
                    asset = unreal.EditorAssetLibrary.load_asset(node)
                    asset_class_name = asset.__class__.__name__
                    suffix = '_{}'.format(
                        ''.join(
                            random.choice(
                                string.ascii_uppercase + string.digits
                            )
                            for _ in range(16)
                        )
                    )
                    asset_name = os.path.splitext(node)[0]
                    new_name = '{}{}'.format(asset_name, suffix)
                    self.logger.debug(
                        'Renaming object: {} > temp: {}'.format(
                            asset_name, new_name
                        )
                    )
                    if not unreal_utils.rename_node_with_suffix(
                            asset_name, suffix
                    ):
                        raise Exception(
                            'Unreal asset {} could not be renamed.'.format(node)
                        )
                    # Supply the new name to the result together with Unreal class name so newly loaded assets can be mapped
                    # during consolidate
                    # TODO: if this isn't properly working,
                    #  temporary_assets[node] = str(new_name) and try to match
                    #  the new imported nodes with the old name.
                    temporary_assets[str(new_name)] = asset_class_name
                    # Remove dcc metadata tag.
                    unreal.EditorAssetLibrary.remove_metadata_tag(
                        asset, asset_const.NODE_METADATA_TAG
                    )
                    status = core_constants.SUCCESS_STATUS
                else:
                    self.logger.warning(
                        'Could not rename none existing object: {}'.format(
                            node
                        )
                    )
            except Exception as error:
                message = str(
                    'Node: {0} could not be renamed, error: {1}'.format(
                        node, error
                    )
                )
                self.logger.error(message)
                status = core_constants.ERROR_STATUS

        bool_status = core_constants.status_bool_mapping[status]
        if not bool_status:
            end_time = time.time()
            total_time = end_time - start_time

            result_data['status'] = status
            result_data['result'] = result
            result_data['execution_time'] = total_time
            result_data['message'] = message

            self._notify_client(plugin, result_data)
            return status, result

        # Change version
        super_status, super_result = super(UnrealAssetManagerEngine, self).change_version(
            asset_info=asset_info, options=options, plugin=plugin
        )

        bool_status = core_constants.status_bool_mapping[super_status]
        if not bool_status:
            end_time = time.time()
            total_time = end_time - start_time

            result_data['status'] = super_status
            result_data['result'] = super_result
            result_data['execution_time'] = total_time
            result_data['message'] = message

            self._notify_client(plugin, result_data)
            return status, result

        # Consolidate new nodes and remove temp ones
        new_nodes = (
                unreal_utils.get_connected_nodes_from_dcc_object(
                    self.dcc_object.name
                )
                or []
        )

        # Consolidate nodes
        unprocessed_nodes = []
        for node in new_nodes:
            temp_node = None
            try:
                asset = unreal.EditorAssetLibrary.load_asset(node)
                asset_class_name = asset.__class__.__name__
                temp_nodes = list(
                    filter(
                        lambda x: temporary_assets[x] == asset_class_name, temporary_assets
                    )
                )
                if not temp_nodes:
                    unprocessed_nodes.append(node)
                    self.logger.debug(
                        "Can't find a matching asset "
                        "for node {} in list {}".format(
                            node, list(temporary_assets.keys())
                        )
                    )
                    continue
                temp_node = temp_nodes[0]
                temp_asset = unreal.EditorAssetLibrary.load_asset(temp_node)
                self.logger.info(
                    'Consolidating from previous asset: {}'.format(
                        temp_node
                    )
                )
                # TODO: This command produces residual redirect nodes.
                #  Can't currently be removed as their creation is delayed and
                #  can't be detected here.
                unreal.EditorAssetLibrary.consolidate_assets(
                    asset, [temp_asset]
                )
            except Exception as error:
                message = str(
                    'Error ocurred during the asset consolidation of {} with {} '
                    '\n Error: {}'.format( node, temp_node, error)
                )
                self.logger.error(message)
                status = core_constants.ERROR_STATUS

        # Clean up not consolidated nodes
        for temp_node in list(temporary_assets.keys()):
            if unreal_utils.node_exists(temp_node):
                self.logger.debug("Removing temp node {}".format(temp_node))
                unreal_utils.delete_node(temp_node)

        if unprocessed_nodes:
            self.logger.warning(
                "Following nodes couldn't be consolidated.\n"
                "List of unprocessed nodes: {} \n"
                "Dictionary of old nodes: {}".format(
                    unprocessed_nodes, temporary_assets
                )
            )
        else:
            self.logger.debug("All nodes consolidation done.")

        end_time = time.time()
        total_time = end_time - start_time

        result_data['status'] = status
        result_data['result'] = super_result
        result_data['execution_time'] = total_time
        result_data['message'] = message

        self._notify_client(plugin, result_data)

        return status, result

    @unreal_utils.run_in_main_thread
    def unload_asset(self, asset_info, options=None, plugin=None):
        '''
        Removes the given *asset_info* from the scene.
        Returns status and result
        '''
        start_time = time.time()
        status = core_constants.UNKNOWN_STATUS
        result = []
        message = None

        plugin_type = core_constants.PLUGIN_AM_ACTION_TYPE
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

        nodes = (
            unreal_utils.get_connected_nodes_from_dcc_object(
                self.dcc_object.name
            )
            or []
        )

        for node in nodes:
            self.logger.debug("Removing object: {}".format(node))
            try:
                if unreal_utils.node_exists(node):
                    if not unreal_utils.delete_node(node):
                        raise Exception(
                            'Unreal asset could not be deleted from library.'
                        )
                    result.append(str(node))
                    status = core_constants.SUCCESS_STATUS
            except Exception as error:
                message = str(
                    'Node: {0} could not be deleted, error: {1}'.format(
                        node, error
                    )
                )
                self.logger.error(message)
                status = core_constants.ERROR_STATUS

            bool_status = core_constants.status_bool_mapping[status]
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

    @unreal_utils.run_in_main_thread
    def remove_asset(self, asset_info, options=None, plugin=None):
        '''
        Removes the given *asset_info* from the scene.
        Returns status and result
        '''
        start_time = time.time()
        status = core_constants.UNKNOWN_STATUS
        result = []
        message = None

        plugin_type = core_constants.PLUGIN_AM_ACTION_TYPE
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

        nodes = (
            unreal_utils.get_connected_nodes_from_dcc_object(
                self.dcc_object.name
            )
            or []
        )

        for node in nodes:
            self.logger.debug("Removing object: {}".format(node))
            try:
                if unreal_utils.node_exists(node):
                    if not unreal_utils.delete_node(node):
                        raise Exception(
                            'Unreal asset could not be deleted from library.'
                        )
                    result.append(str(node))
                    status = core_constants.SUCCESS_STATUS
            except Exception as error:
                message = str(
                    'Node: {0} could not be deleted, error: {1}'.format(
                        node, error
                    )
                )
                self.logger.error(message)
                status = core_constants.ERROR_STATUS

            bool_status = core_constants.status_bool_mapping[status]
            if not bool_status:
                end_time = time.time()
                total_time = end_time - start_time

                result_data['status'] = status
                result_data['result'] = result
                result_data['execution_time'] = total_time
                result_data['message'] = message

                self._notify_client(plugin, result_data)
                return status, result

        if unreal_utils.ftrack_node_exists(self.dcc_object.name):
            try:
                unreal_utils.delete_ftrack_node(self.dcc_object.name)
                result.append(str(self.dcc_object.name))
                status = core_constants.SUCCESS_STATUS
            except Exception as error:
                message = str(
                    'Could not delete the dcc_object, error: {}'.format(error)
                )
                self.logger.error(message)
                status = core_constants.ERROR_STATUS

            bool_status = core_constants.status_bool_mapping[status]
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
