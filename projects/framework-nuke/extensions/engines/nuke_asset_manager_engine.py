# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import time
import nuke

from ftrack_framework_asset_manager.engines.asset_manager_engine import (
    AssetManagerEngine,
)
from ftrack_framework_asset_manager.asset.ftrack_asset_info import (
    FtrackAssetInfo,
)
from ftrack_framework_nuke import utils as nuke_utils
from ftrack_framework_nuke.asset import constants as asset_const
from ftrack_framework_nuke.asset import NukeFtrackObjectManager
from ftrack_framework_nuke.asset.dcc_object import NukeDccObject


class NukeAssetManagerEngine(AssetManagerEngine):
    name = 'nuke_asset_manager_engine'
    engine_types = ['asset_manager']

    FtrackObjectManager = NukeFtrackObjectManager
    '''FtrackObjectManager class to use'''
    DccObject = NukeDccObject
    '''DccObject class to use'''

    def __init__(
        self,
        plugin_registry,
        session,
        context_id=None,
        on_plugin_executed=None,
    ):
        '''Initialise AssetManagerEngine with *plugin_registry*, *session*, *context_id*, and *on_plugin_executed*'''
        super(NukeAssetManagerEngine, self).__init__(
            plugin_registry,
            session,
            context_id,
            on_plugin_executed=on_plugin_executed,
        )

    @nuke_utils.run_in_main_thread
    def discover_assets(self, assets=None, options=None, plugin=None):
        '''
        Discover all the assets in the scene:
        Returns status and result
        '''
        start_time = time.time()
        status = 'unknown'
        result = []
        message = None

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
                status = 'error'
            else:
                status = 'success'
        else:
            self.logger.debug("No assets in the scene")
            status = 'success'

        result = ftrack_asset_info_list

        end_time = time.time()
        total_time = end_time - start_time

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
        status = 'unknown'
        result = []
        message = None

        self.asset_info = asset_info
        dcc_object = self.DccObject(
            from_id=asset_info[asset_const.ASSET_INFO_ID]
        )
        self.dcc_object = dcc_object

        if options.get('clear_selection'):
            nuke_utils.clean_selection()

        ftrack_node = nuke.toNode(self.dcc_object.name)

        parented_nodes = ftrack_node.getNodes()
        parented_nodes_names = [x.knob('name').value() for x in parented_nodes]
        nodes_to_select_str = ftrack_node.knob(asset_const.ASSET_LINK).value()
        nodes_to_select = parented_nodes_names
        if len(nodes_to_select_str) > 0:
            nodes_to_select = set(
                nodes_to_select + nodes_to_select_str.split(";")
            )

        for node_name in nodes_to_select:
            try:
                node_to_select = nuke.toNode(node_name)
                node_to_select['selected'].setValue(True)
                result.append(str(node_name))
                status = 'success'
            except Exception as error:
                message = str(
                    'Could not select the node {}, error: {}'.format(
                        str(node_name), error
                    )
                )
                self.logger.error(message)
                status = 'error'

            bool_status = status == 'success'
            if not bool_status:
                end_time = time.time()
                total_time = end_time - start_time
                return status, result

        try:
            ftrack_node['selected'].setValue(True)
            result.append(str(ftrack_node))
            status = 'success'
        except Exception as error:
            message = str(
                'Could not select the dcc_object, error: {}'.format(error)
            )
            self.logger.error(message)
            status = 'error'

        end_time = time.time()
        total_time = end_time - start_time

        return status, result

    @nuke_utils.run_in_main_thread
    def select_assets(self, assets, options=None, plugin=None):
        '''
        Returns status dictionary and results dictionary keyed by the id for
        executing the :meth:`select_asset` for all the
        :class:`~ftrack_framework_asset_manager.asset.FtrackAssetInfo` in the given
        *assets* list.

        *assets*: List of :class:`~ftrack_framework_asset_manager.asset.FtrackAssetInfo`
        '''
        return super(NukeAssetManagerEngine, self).select_assets(
            assets=assets, options=options, plugin=plugin
        )

    @nuke_utils.run_in_main_thread
    def unload_asset(self, asset_info, options=None, plugin=None):
        '''
        Removes the given *asset_info* from the scene.
        Returns status and result
        '''
        start_time = time.time()
        status = 'unknown'
        result = []
        message = None

        self.asset_info = asset_info
        dcc_object = self.DccObject(
            from_id=asset_info[asset_const.ASSET_INFO_ID]
        )
        self.dcc_object = dcc_object

        ftrack_node = nuke.toNode(self.dcc_object.name)
        if not ftrack_node:
            message = "There is no ftrack object"
            self.logger.debug(message)
            status = 'unknown'
            return status, result

        if ftrack_node.Class() == 'BackdropNode':
            parented_nodes = ftrack_node.getNodes()
            parented_nodes_names = [
                x.knob('name').value() for x in parented_nodes
            ]
            nodes_to_delete_str = ftrack_node.knob(
                asset_const.ASSET_LINK
            ).value()
            nodes_to_delete = parented_nodes_names
            if len(nodes_to_delete_str) > 0:
                nodes_to_delete = set(
                    nodes_to_delete + nodes_to_delete_str.split(";")
                )
            for node_name in nodes_to_delete:
                node_to_delete = nuke.toNode(node_name)
                self.logger.debug(
                    "removing : {}".format(node_to_delete.Class())
                )
                try:
                    nuke.delete(node_to_delete)
                    result.append(str(node_name))
                    status = 'success'
                except Exception as error:
                    message = str(
                        'Could not delete the node {}, error: {}'.format(
                            str(node_name), error
                        )
                    )
                    self.logger.error(message)
                    status = 'error'

                bool_status = status == 'success'
                if not bool_status:
                    end_time = time.time()
                    total_time = end_time - start_time
                    return status, result

        bool_status = status == 'success'
        if not bool_status:
            end_time = time.time()
            total_time = end_time - start_time
            return status, result

        self.ftrack_object_manager.objects_loaded = False

        end_time = time.time()
        total_time = end_time - start_time

        return status, result

    @nuke_utils.run_in_main_thread
    def remove_asset(self, asset_info, options=None, plugin=None):
        '''
        Removes the given *asset_info* from the scene.
        Returns status and result
        '''
        start_time = time.time()
        status = 'unknown'
        result = []
        message = None

        self.asset_info = asset_info
        dcc_object = self.DccObject(
            from_id=asset_info[asset_const.ASSET_INFO_ID]
        )
        self.dcc_object = dcc_object

        ftrack_node = nuke.toNode(self.dcc_object.name)
        if not ftrack_node:
            message = "There is no ftrack object"
            self.logger.debug(message)
            status = 'unknown'
            return status, result

        if ftrack_node.Class() == 'BackdropNode':
            # Collect and remove all nodes within the backdrop plus the linked
            # nodes
            parented_nodes = ftrack_node.getNodes()
            parented_nodes_names = [
                x.knob('name').value() for x in parented_nodes
            ]
            nodes_to_delete_str = ftrack_node.knob(
                asset_const.ASSET_LINK
            ).value()
            node_names_to_delete = parented_nodes_names
            if len(nodes_to_delete_str or '') > 0:
                node_names_to_delete = set(
                    node_names_to_delete + nodes_to_delete_str.split(";")
                )
            for node_name in node_names_to_delete:
                node_to_delete = nuke.toNode(node_name)
                if not node_to_delete:
                    self.logger.warning(
                        "Can't remove non existing node: {}".format(node_name)
                    )
                    continue
                self.logger.debug(
                    "removing : {}".format(node_to_delete.Class())
                )
                try:
                    nuke.delete(node_to_delete)
                    result.append(str(node_name))
                    status = 'success'
                except Exception as error:
                    message = str(
                        'Could not delete the node {}, error: {}'.format(
                            str(node_name), error
                        )
                    )
                    self.logger.error(message)
                    status = 'error'

                bool_status = status == 'success'
                if not bool_status:
                    end_time = time.time()
                    total_time = end_time - start_time
                    return status, result

        try:
            str_node = str(self.dcc_object.name)
            self.logger.debug("removing : {}".format(str_node))
            nuke.delete(ftrack_node)
            result.append(str_node)
            status = 'success'
        except Exception as error:
            message = str(
                'Could not delete the nuke dcc object, error: {}'.format(error)
            )
            self.logger.error(message)
            status = 'error'

        bool_status = status == 'success'
        if not bool_status:
            end_time = time.time()
            total_time = end_time - start_time
            return status, result

        end_time = time.time()
        total_time = end_time - start_time

        return status, result
