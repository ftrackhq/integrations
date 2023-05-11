# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import time
import maya
import maya.cmds as cmds

from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline.host.engine import AssetManagerEngine
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo

from ftrack_connect_pipeline_maya import utils as maya_utils
from ftrack_connect_pipeline_maya.constants import asset as asset_const
from ftrack_connect_pipeline_maya.constants.asset import modes as modes_const
from ftrack_connect_pipeline_maya.asset import MayaFtrackObjectManager
from ftrack_connect_pipeline_maya.asset.dcc_object import MayaDccObject


class MayaAssetManagerEngine(AssetManagerEngine):
    engine_type = 'asset_manager'

    FtrackObjectManager = MayaFtrackObjectManager
    '''FtrackObjectManager class to use'''
    DccObject = MayaDccObject
    '''DccObject class to use'''

    def __init__(
        self, event_manager, host_types, host_id, asset_type_name=None
    ):
        '''Initialise AssetManagerEngine with *event_manager*, *host*, *hostid*
        and *asset_type_name*'''
        super(MayaAssetManagerEngine, self).__init__(
            event_manager, host_types, host_id, asset_type_name=asset_type_name
        )

    @maya_utils.run_in_main_thread
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

        ftrack_asset_nodes = maya_utils.get_ftrack_nodes()
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
            self.logger.debug("No assets in the scene")
            status = core_constants.SUCCESS_STATUS

        result = ftrack_asset_info_list

        end_time = time.time()
        total_time = end_time - start_time

        result_data['status'] = status
        result_data['result'] = result
        result_data['execution_time'] = total_time

        self._notify_client(plugin, result_data)

        return status, result

    @maya_utils.run_in_main_thread
    def change_version(self, asset_info, options, plugin=None):
        '''
        Returns the :const:`~ftrack_connnect_pipeline.constants.status` and the
        result of changing the version of the given *asset_info* to the new
        version id passed in the given *options*

        *asset_info* : :class:`~ftrack_connect_pipeline.asset.FtrackAssetInfo`

        *options* : Options should contain the new_version_id key with the id
        value

        *plugin* : Default None. Plugin definition, a dictionary with the
        plugin information.
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

        new_version_id = options['new_version_id']

        self.asset_info = asset_info
        dcc_object = self.DccObject(
            from_id=asset_info[asset_const.ASSET_INFO_ID]
        )
        self.dcc_object = dcc_object

        # It's an import, so change version with the main method
        if (
            self.dcc_object.get(asset_const.LOAD_MODE)
            != modes_const.REFERENCE_MODE
        ):
            return super(MayaAssetManagerEngine, self).change_version(
                asset_info=asset_info, options=options, plugin=plugin
            )

        # Unload the reference
        unload_result = None
        unload_status = None
        try:
            unload_status, unload_result = self.unload_asset(
                asset_info=asset_info, options=None, plugin=None
            )
        except Exception as e:
            unload_status = core_constants.ERROR_STATUS
            self.logger.exception(e)
            message = str(
                "Error unloading asset with version id {} \n error: {} "
                "\n asset_info: {}".format(
                    asset_info[asset_const.VERSION_ID], e, asset_info
                )
            )
            self.logger.error(message)

        bool_status = core_constants.status_bool_mapping[unload_status]
        if not bool_status:
            end_time = time.time()
            total_time = end_time - start_time

            result_data['status'] = status
            result_data['result'] = result
            result_data['execution_time'] = total_time
            result_data['message'] = result['message'] = message

            self._notify_client(plugin, result_data)

            return unload_status, unload_result

        # Get reference Node
        reference_node = None
        for obj in unload_result:
            if cmds.nodeType(obj) == 'reference':
                reference_node = unload_result[0]
                break
        if not reference_node:
            return super(MayaAssetManagerEngine, self).change_version(
                asset_info=asset_info, options=options, plugin=plugin
            )

        collect_status = None
        component_path = None
        # Find new reference path
        try:
            # Get Component name from the original asset info
            component_name = self.asset_info.get(asset_const.COMPONENT_NAME)
            # Get asset version entity of the ne_ version_id
            asset_version_entity = self.session.query(
                'select version from AssetVersion where id is "{}"'.format(
                    new_version_id
                )
            ).one()

            # Collect data of the new version
            asset_entity = asset_version_entity['asset']
            asset_id = asset_entity['id']
            version_number = int(asset_version_entity['version'])
            asset_name = asset_entity['name']
            asset_type_name = asset_entity['type']['name']
            version_id = asset_version_entity['id']
            location = asset_version_entity.session.pick_location()
            component_path = None
            for component in asset_version_entity['components']:
                if component['name'] == component_name:
                    if location.get_component_availability(component) == 100.0:
                        component_path = location.get_filesystem_path(
                            component
                        )
            if component_path:
                collect_status = core_constants.SUCCESS_STATUS
            else:
                collect_status = core_constants.ERROR_STATUS
                message = "Component is not available in your location, please transfer over"
        except Exception as e:
            collect_status = core_constants.ERROR_STATUS
            self.logger.exception(e)
            message = str(
                "Error getting the new component path of asset with version id {} \n error: {} "
                "\n asset_info: {}".format(
                    asset_info[asset_const.VERSION_ID], e, asset_info
                )
            )
            self.logger.error(message)

        bool_status = core_constants.status_bool_mapping[collect_status]
        if not bool_status:
            end_time = time.time()
            total_time = end_time - start_time

            result_data['status'] = status
            result_data['result'] = result
            result_data['execution_time'] = total_time
            result_data['message'] = result['message'] = message

            self._notify_client(plugin, result_data)

            return collect_status, result

        update_status = None
        try:
            # update reference
            cmds.file(component_path, loadReference=reference_node)
            update_status = core_constants.SUCCESS_STATUS
        except Exception as e:
            update_status = core_constants.ERROR_STATUS
            self.logger.exception(e)
            message = str(
                "Error reloading the reference of the asset with version id {} \n error: {} "
                "\n asset_info: {}".format(
                    asset_info[asset_const.VERSION_ID], e, asset_info
                )
            )
            self.logger.error(message)

        bool_status = core_constants.status_bool_mapping[update_status]
        if not bool_status:
            end_time = time.time()
            total_time = end_time - start_time

            result_data['status'] = status
            result_data['result'] = result
            result_data['execution_time'] = total_time
            result_data['message'] = result['message'] = message

            self._notify_client(plugin, result_data)

            return update_status, result

        # Reload asset
        try:
            maya_utils.load_reference_node(reference_node)
            status = core_constants.SUCCESS_STATUS
        except Exception as error:
            message = str(
                'Could not load the reference node {}, error: {}'.format(
                    str(reference_node), error
                )
            )
            self.logger.error(message)
            status = core_constants.ERROR_STATUS

        bool_status = core_constants.status_bool_mapping[update_status]
        if bool_status:
            # update ftrack Node
            try:
                self.ftrack_object_manager.objects_loaded = True
                self.ftrack_object_manager.dcc_object[
                    asset_const.ASSET_ID
                ] = asset_id
                self.ftrack_object_manager.dcc_object[
                    asset_const.VERSION_NUMBER
                ] = version_number
                self.ftrack_object_manager.dcc_object[
                    asset_const.ASSET_NAME
                ] = asset_name
                self.ftrack_object_manager.dcc_object[
                    asset_const.ASSET_TYPE_NAME
                ] = asset_type_name
                self.ftrack_object_manager.dcc_object[
                    asset_const.VERSION_ID
                ] = version_id

                self.ftrack_object_manager.asset_info[
                    asset_const.ASSET_ID
                ] = asset_id
                self.ftrack_object_manager.asset_info[
                    asset_const.VERSION_NUMBER
                ] = version_number
                self.ftrack_object_manager.asset_info[
                    asset_const.ASSET_NAME
                ] = asset_name
                self.ftrack_object_manager.asset_info[
                    asset_const.ASSET_TYPE_NAME
                ] = asset_type_name
                self.ftrack_object_manager.asset_info[
                    asset_const.VERSION_ID
                ] = version_id

                status = core_constants.SUCCESS_STATUS
            except Exception as error:
                message = str(
                    'Could not update ftrack node {}, error: {}'.format(
                        str(reference_node), error
                    )
                )
                self.logger.error(message)
                status = core_constants.ERROR_STATUS
        end_time = time.time()
        total_time = end_time - start_time

        result[
            asset_info[asset_const.ASSET_INFO_ID]
        ] = self.ftrack_object_manager.asset_info

        result_data['status'] = status
        result_data['result'] = result
        result_data['execution_time'] = total_time
        result_data['message'] = result['message'] = message

        self._notify_client(plugin, result_data)

        return status, result

    @maya_utils.run_in_main_thread
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

        if options.get('clear_selection'):
            cmds.select(cl=True)

        nodes = cmds.listConnections(
            '{}.{}'.format(self.dcc_object.name, asset_const.ASSET_LINK)
        )
        for node in nodes:
            try:
                cmds.select(node, add=True)
                result.append(str(node))
                status = core_constants.SUCCESS_STATUS
            except Exception as error:
                message = str(
                    'Could not select the node {}, error: {}'.format(
                        str(node), error
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
                result_data['message'] = result['message'] = message

                self._notify_client(plugin, result_data)
                return status, result

        end_time = time.time()
        total_time = end_time - start_time

        result_data['status'] = status
        result_data['result'] = result
        result_data['execution_time'] = total_time

        self._notify_client(plugin, result_data)

        return status, result

    @maya_utils.run_in_main_thread
    def select_assets(self, assets, options=None, plugin=None):
        '''
        Returns status dictionary and results dictionary keyed by the id for
        executing the :meth:`select_asset` for all the
        :class:`~ftrack_connect_pipeline.asset.FtrackAssetInfo` in the given
        *assets* list.

        *assets*: List of :class:`~ftrack_connect_pipeline.asset.FtrackAssetInfo`
        '''
        return super(MayaAssetManagerEngine, self).select_assets(
            assets=assets, options=options, plugin=plugin
        )

    @maya_utils.run_in_main_thread
    def load_asset(self, asset_info, options=None, plugin=None):
        '''
        Override load_asset method to deal with unloaded references.
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
            'method': 'load_asset',
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

        # It's an import, so load asset with the main method
        if (
            self.dcc_object.get(asset_const.LOAD_MODE)
            != modes_const.REFERENCE_MODE
        ):
            return super(MayaAssetManagerEngine, self).load_asset(
                asset_info=asset_info, options=options, plugin=plugin
            )

        # Find the reference node if the reference has been unloaded
        reference_node = False
        nodes = (
            cmds.listConnections(
                '{}.{}'.format(self.dcc_object.name, asset_const.ASSET_LINK)
            )
            or []
        )

        for node in nodes:
            if cmds.nodeType(node) == 'reference':
                reference_node = maya_utils.get_reference_node(node)
                if reference_node:
                    break

        # Load asset with the main method, the reference has not been created yet.
        if not reference_node:
            return super(MayaAssetManagerEngine, self).load_asset(
                asset_info=asset_info, options=options, plugin=plugin
            )

        try:
            maya_utils.load_reference_node(reference_node)
            result.append(str(reference_node))
            status = core_constants.SUCCESS_STATUS
        except Exception as error:
            message = str(
                'Could not load the reference node {}, error: {}'.format(
                    str(reference_node), error
                )
            )
            self.logger.error(message)
            status = core_constants.ERROR_STATUS

        bool_status = core_constants.status_bool_mapping[status]
        if bool_status:
            self.ftrack_object_manager.objects_loaded = True

        end_time = time.time()
        total_time = end_time - start_time

        result_data['status'] = status
        result_data['result'] = result
        result_data['execution_time'] = total_time
        result_data['message'] = message

        self._notify_client(plugin, result_data)
        return status, result

    @maya_utils.run_in_main_thread
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

        reference_node = False
        nodes = (
            cmds.listConnections(
                '{}.{}'.format(self.dcc_object.name, asset_const.ASSET_LINK)
            )
            or []
        )
        if self.dcc_object.name in nodes:
            nodes.remove(self.dcc_object.name)

        for node in nodes:
            if cmds.nodeType(node) == 'reference':
                reference_node = maya_utils.get_reference_node(node)
                if reference_node:
                    break

        if reference_node:
            self.logger.debug("Removing reference: {}".format(reference_node))
            try:
                maya_utils.unload_reference_node(reference_node)
                result.append(str(reference_node))
                status = core_constants.SUCCESS_STATUS
            except Exception as error:
                message = str(
                    'Could not remove the reference node {}, error: {}'.format(
                        str(reference_node), error
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
        else:
            for node in nodes:
                self.logger.debug("Removing object: {}".format(node))
                try:
                    if maya_utils.obj_exists(node):
                        maya_utils.delete_object(node)
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

    @maya_utils.run_in_main_thread
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

        reference_node = False
        nodes = (
            cmds.listConnections(
                '{}.{}'.format(self.dcc_object.name, asset_const.ASSET_LINK)
            )
            or []
        )
        for node in nodes:
            if cmds.nodeType(node) == 'reference':
                reference_node = maya_utils.get_reference_node(node)
                if reference_node:
                    break

        if reference_node:
            self.logger.debug("Removing reference: {}".format(reference_node))
            try:
                maya_utils.remove_reference_node(reference_node)
                result.append(str(reference_node))
                status = core_constants.SUCCESS_STATUS
            except Exception as error:
                message = str(
                    'Could not remove the reference node {}, error: {}'.format(
                        str(reference_node), error
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
        else:
            for node in nodes:
                self.logger.debug("Removing object: {}".format(node))
                try:
                    if maya_utils.obj_exists(node):
                        maya_utils.delete_object(node)
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

        if maya_utils.obj_exists(self.dcc_object.name):
            try:
                maya_utils.delete_object(self.dcc_object.name)
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
                result_data['message'] = result['message'] = message

                self._notify_client(plugin, result_data)

                return status, result

        end_time = time.time()
        total_time = end_time - start_time

        result_data['status'] = status
        result_data['result'] = result
        result_data['execution_time'] = total_time

        self._notify_client(plugin, result_data)

        return status, result
