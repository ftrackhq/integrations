# # :coding: utf-8
# # :copyright: Copyright (c) 2019 ftrack

import json

from ftrack_connect_pipeline.asset import FtrackAssetInfo, FtrackAssetBase
from ftrack_connect_pipeline_maya.constants import asset as asset_const
from ftrack_connect_pipeline import constants as core_const
from ftrack_connect_pipeline_maya.utils import custom_commands as maya_utils
from ftrack_connect_pipeline_maya.constants.asset import modes as load_const

import ftrack_api
import maya.cmds as cmd

class FtrackAssetNode(FtrackAssetBase):
    '''
    Base FtrackAssetNode class.
    '''

    def is_sync(self):
        return self._check_node_sync()

    def __init__(self, event_manager):
        '''
        Initialize FtrackAssetNode with *ftrack_asset_info*, and *session*.

        *ftrack_asset_info* should be the
        :class:`ftrack_connect_pipeline.asset.asset_info.FtrackAssetInfo`
        instance.
        *session* should be the :class:`ftrack_api.session.Session` instance
        to use for communication with the server.
        '''
        super(FtrackAssetNode, self).__init__(event_manager)
        # self.listen_asset_manager_actions()

    def init_node(self):
        '''
        Return the ftrack node for this class. It checks if there is already a
        matching ftrack node in the scene, in this case it updates the node if
        it's not. In case there is no node in the scene this function creates a
        new one.
        '''
        scene_node = self.get_ftrack_node_from_scene()
        if scene_node:
            self._set_node(scene_node)
            if not self.is_sync():
                self._update_node()
        else:
            self.create_new_node()

        return self.node

    def _get_parameters_dictionary(self, maya_obj):
        param_dict = {}
        all_attr = cmd.listAttr(maya_obj, c=True, se=True)
        for attr in all_attr:
            if cmd.attributeQuery(attr, node=maya_obj, msg=True):
                continue
            attr_value = cmd.getAttr('{}.{}'.format(maya_obj, attr))
            param_dict[attr] = attr_value
        return param_dict

    def get_ftrack_node_from_scene(self):
        '''
        Return the ftrack node of the current asset_version of the scene if
        exists.
        '''
        ftrack_asset_nodes = maya_utils.get_ftrack_nodes()
        for ftrack_node in ftrack_asset_nodes:

            param_dict = self._get_parameters_dictionary(ftrack_node)
            node_asset_info = FtrackAssetInfo(param_dict)
            if node_asset_info.is_deprecated:
                raise DeprecationWarning("Can not read v1 ftrack asset plugin")
            if (
                    node_asset_info[asset_const.COMPONENT_ID] ==
                    self.asset_info[asset_const.COMPONENT_ID]
            ):

                return ftrack_node

    def _check_node_sync(self):
        '''
        Check if the current parameters of the ftrack node match the values
        of the asset_info.

        '''
        if not self.node:
            self.logger.warning("Can't check if ftrack node is not loaded")
            return False

        synced = False

        param_dict = self._get_parameters_dictionary(self.node)
        node_asset_info = FtrackAssetInfo(param_dict)

        if node_asset_info == self.asset_info:
            self.logger.debug("{} is synced".format(self.node))
            synced = True

        return synced


    def _get_unique_node_name(self):
        '''
        Return a unique scene name for the current asset_name
        '''
        ftrack_node_name = '{}_ftrackdata'.format(
            self.asset_info[asset_const.ASSET_NAME]
        )
        count = 0
        while 1:
            if cmd.objExists(ftrack_node_name):
                ftrack_node_name = ftrack_node_name + str(count)
                count = count + 1
            else:
                break
        return ftrack_node_name


    def connect_objects(self, objects):
        '''
        Parent the given *objects* under current ftrack_node

        *objects* is List type of INode
        '''
        for obj in objects:
            if cmd.lockNode(obj, q=True)[0]:
                cmd.lockNode(obj, l=False)

            if not cmd.attributeQuery('ftrack', n=obj, exists=True):
                cmd.addAttr(obj, ln='ftrack', at='message')

            if not cmd.listConnections('{}.ftrack'.format(obj)):
                cmd.connectAttr(
                    '{}.{}'.format(self.node, asset_const.ASSET_LINK),
                    '{}.ftrack'.format(obj)
                )


    def get_load_mode_from_node(self, node):
        '''Return the import mode used to import an asset.'''
        load_mode = cmd.getAttr('{}.{}'.format(
            node, asset_const.LOAD_MODE)
        )
        return load_mode


    def create_new_node(self):
        '''
        Creates the ftrack_node with a unique name. The ftrack node is type of
        FtrackAssetHelper.

        '''

        name = self._get_unique_node_name()
        self._node = cmd.createNode('ftrackAssetNode', name=name)
        self._nodes.append(self.node)

        return self._update_node()


    def _update_node(self):
        '''Update the parameters of the ftrack node. And Return the ftrack node
        updated
        '''
        for k, v in self.asset_info.items():
            if k == asset_const.VERSION_NUMBER:
                cmd.setAttr('{}.{}'.format(self.node, k), v, l=True)
            else:
                cmd.setAttr('{}.{}'.format(self.node, k), v, type="string", l=True)

        return self.node

    def _change_version(self, event):
        '''
        Override function from the main class, remove the current assets of the
        scene and loads the given version of the asset in the *event*. Then
        super the base function.
        '''
        asset_info = event['data']

        try:
            self.logger.debug("Removing current objects")
            self.remove_current_objects()
        except Exception, e:
            self.logger.error("Error removing current objects: {}".format(e))


        asset_info_options = json.loads(
            self.asset_info[asset_const.ASSET_INFO_OPTIONS].decode('base64')
        )
        asset_context = asset_info_options['settings']['context']
        asset_data = asset_info[asset_const.COMPONENT_PATH]
        asset_context[asset_const.ASSET_ID] = asset_info[asset_const.ASSET_ID]
        asset_context[asset_const.VERSION_NUMBER] = asset_info[asset_const.VERSION_NUMBER]
        asset_context[asset_const.ASSET_NAME] = asset_info[asset_const.ASSET_NAME]
        asset_context[asset_const.ASSET_TYPE] = asset_info[asset_const.ASSET_TYPE]
        asset_context[asset_const.VERSION_ID] = asset_info[asset_const.VERSION_ID]

        asset_info_options['settings']['data'] = [asset_data]
        asset_info_options['settings']['context'].update(asset_context)


        run_event = ftrack_api.event.base.Event(
            topic=core_const.PIPELINE_RUN_PLUGIN_TOPIC,
            data=asset_info_options
        )
        plugin_result_data = self.session.event_hub.publish(
            run_event,
            synchronous=True
        )
        result_data = plugin_result_data[0]
        if not result_data:
            self.logger.error("Error re-loading asset")

        super(FtrackAssetNode, self)._change_version(event)

    def discover_assets(self):
        '''
        Returns *asset_info_list* with all the assets loaded in the current
        scene that has an ftrackAssetNode connected
        '''
        ftrack_asset_nodes = maya_utils.get_ftrack_nodes()

        asset_info_list = []

        for ftrack_node in ftrack_asset_nodes:

            param_dict = self._get_parameters_dictionary(ftrack_node)
            node_asset_info = FtrackAssetInfo(param_dict)
            asset_info_list.append(node_asset_info)
        return asset_info_list

    def remove_current_objects(self):
        '''
        Remove all the imported or referenced objects in the scene
        '''
        referenceNode = False
        for node in cmd.listConnections(
                '{}.{}'.format(self.node, asset_const.ASSET_LINK)
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
                '{}.{}'.format(self.node, asset_const.ASSET_LINK)
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
        if cmd.objExists(self.node):
            cmd.delete(self.node)
