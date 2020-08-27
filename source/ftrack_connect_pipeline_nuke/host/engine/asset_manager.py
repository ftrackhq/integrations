# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import nuke
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.host.engine import AssetManagerEngine
from ftrack_connect_pipeline_nuke.asset import FtrackAssetTab
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo
from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils
from ftrack_connect_pipeline_nuke.constants import asset as asset_const


class NukeAssetManagerEngine(AssetManagerEngine):
    ftrack_asset_class = FtrackAssetTab
    engine_type = 'asset_manager'

    def __init__(self, event_manager, host, hostid, asset_type=None):
        '''Initialise AssetManagerEngine with *event_manager*, *host*, *hostid*
        and *asset_type*'''
        super(NukeAssetManagerEngine, self).__init__(
            event_manager, host, hostid, asset_type=asset_type
        )

    def discover_assets(self, assets=None, options=None, plugin=None):
        '''
        Discover all the assets in the scene:
        Returns status and result
        '''
        status = constants.UNKNOWN_STATUS
        ftrack_asset_nodes = nuke_utils.get_nodes_with_ftrack_tab()
        ftrack_asset_info_list = []

        for ftrack_object in ftrack_asset_nodes:
            param_dict = FtrackAssetTab.get_parameters_dictionary(
                ftrack_object
            )
            node_asset_info = FtrackAssetInfo(param_dict)
            ftrack_asset_info_list.append(node_asset_info)

        if not ftrack_asset_info_list:
            status = constants.ERROR_STATUS
        else:
            status = constants.SUCCESS_STATUS
        result = ftrack_asset_info_list

        return status, result

    def remove_asset(self, asset_info, options=None, plugin=None):
        '''
        Removes the given *asset_info* from the scene.
        Returns status and result
        '''
        status = constants.UNKNOWN_STATUS
        result = []
        ftrack_asset_object = self.get_ftrack_asset_object(asset_info)

        ftrack_object = nuke.toNode(ftrack_asset_object.ftrack_object)
        if not ftrack_object:
            self.logger.info("There is no ftrack object")
            status = constants.UNKNOWN_STATUS
            return status, result

        if ftrack_object.Class() == 'BackdropNode':
            parented_nodes = ftrack_object.getNodes()
            parented_nodes_names = [x.knob('name').value() for x in
                                    parented_nodes]
            nodes_to_delete_str = ftrack_object.knob(
                asset_const.ASSET_LINK
            ).value()
            nodes_to_delete = nodes_to_delete_str.split(";")
            nodes_to_delete = set(nodes_to_delete + parented_nodes_names)
            for node_s in nodes_to_delete:
                node = nuke.toNode(node_s)
                self.logger.info("removing : {}".format(node.Class()))
                try:
                    nuke.delete(node)
                    result.append(str(node_s))
                    status = constants.SUCCESS_STATUS
                except Exception as error:
                    self.logger.error(
                        'Could not delete the node {}, error: {}'.format(
                            str(node_s), error)
                    )
                    status = constants.ERROR_STATUS

            bool_status = constants.status_bool_mapping[status]
            if not bool_status:
                return status, result

        try:
            str_node = str(ftrack_asset_object.ftrack_object)
            nuke.delete(ftrack_object)
            result.append(str_node)
            status = constants.SUCCESS_STATUS
        except Exception as error:
            self.logger.error(
                'Could not delete the ftrack_object, error: {}'.format(error)
            )
            status = constants.ERROR_STATUS

        bool_status = constants.status_bool_mapping[status]
        if not bool_status:
            return status, result

        return status, result

    def select_asset(self, asset_info, options=None, plugin=None):
        '''
        Selects the given *asset_info* from the scene.
        *options* can contain clear_selection to clear the selection before
        select the given *asset_info*.
        Returns status and result
        '''
        status = constants.UNKNOWN_STATUS
        result = []

        ftrack_asset_object = self.get_ftrack_asset_object(asset_info)

        if options.get('clear_selection'):
            nuke_utils.cleanSelection()

        ftrack_object = nuke.toNode(ftrack_asset_object.ftrack_object)

        parented_nodes = ftrack_object.getNodes()
        parented_nodes_names = [x.knob('name').value() for x in parented_nodes]
        nodes_to_select_str = ftrack_object.knob(
            asset_const.ASSET_LINK
        ).value()
        nodes_to_select = nodes_to_select_str.split(";")
        nodes_to_select = set(nodes_to_select + parented_nodes_names)

        for node_s in nodes_to_select:
            try:
                node = nuke.toNode(node_s)
                node['selected'].setValue(True)
                result.append(str(node_s))
                status = constants.SUCCESS_STATUS
            except Exception as error:
                self.logger.error(
                    'Could not select the node {}, error: {}'.format(
                        str(node_s), error)
                )
                status = constants.ERROR_STATUS

            bool_status = constants.status_bool_mapping[status]
            if not bool_status:
                return status, result

        try:
            ftrack_object['selected'].setValue(True)
            result.append(str(ftrack_object))
            status = constants.SUCCESS_STATUS
        except Exception as error:
            self.logger.error(
                'Could not select the ftrack_object, error: {}'.format(error)
            )
            status = constants.ERROR_STATUS

        bool_status = constants.status_bool_mapping[status]
        if not bool_status:
            return status, result

        return status, result
