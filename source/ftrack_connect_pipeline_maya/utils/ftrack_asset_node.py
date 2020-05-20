from ftrack_connect_pipeline.asset import FtrackAssetInfo, FtrackAssetBase
from ftrack_connect_pipeline.constants import asset as asset_const
import custom_commands as maya_utils

import maya.cmds as cmd

class FtrackAssetNode(FtrackAssetBase):
    '''
    Base FtrackAssetNode class.
    '''

    def is_sync(self):
        return self._check_node_sync()

    def __init__(self, ftrack_asset_info, session):
        '''
        Initialize FtrackAssetNode with *ftrack_asset_info*, and *session*.

        *ftrack_asset_info* should be the
        :class:`ftrack_connect_pipeline.asset.asset_info.FtrackAssetInfo`
        instance.
        *session* should be the :class:`ftrack_api.session.Session` instance
        to use for communication with the server.
        '''
        super(FtrackAssetNode, self).__init__(ftrack_asset_info, session)

        self.nodes = []
        self.node = None

    def init_node(self):
        '''
        Return the ftrack node for this class. It checks if there is already a
        matching ftrack node in the scene, in this case it updates the node if
        it's not. In case there is no node in the scene this function creates a
        new one.
        '''
        scene_node = self.get_ftrack_node_from_scene()
        if scene_node:
            self.set_node(scene_node)
            if not self.is_sync():
                self._update_node()
        else:
            self.create_new_node()

        return self.node

    def _get_parameters_dictionary(self, maya_obj):
        param_dict = {}
        all_attr = cmd.listAttr(maya_obj, c=True, fp=True)
        for attr in all_attr:
            attr_value = cmd.getAttr('{}.{}'.fromat(maya_obj, attr))
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
                #TODO: do something with the deprecated
                raise NotImplementedError("Can not read v1 ftrack asset plugin")
            if (
                    node_asset_info[asset_const.COMPONENT_ID] ==
                    self.asset_info[asset_const.COMPONENT_ID]
            ):

                return ftrack_node


    def set_node(self, ftrack_node):
        '''
        Sets the given *ftrack_node* as the current self.node of the class
        '''
        self.node = ftrack_node

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
                    '{}.assetLink'.format(self.node),
                    '{}.ftrack'.format(obj)
                )


    def get_load_mode_from_node(self, node):
        '''Return the import mode used to import an asset.'''
        load_mode = cmd.getAttr('{}.{}'.fromat(
            node, asset_const.ASSET_INFO_OPTIONS)
        )
        return load_mode


    def create_new_node(self):
        '''
        Creates the ftrack_node with a unique name. The ftrack node is type of
        FtrackAssetHelper.

        '''

        name = self._get_unique_node_name()
        self.node = cmd.createNode('ftrackAssetNode', name=name)
        self.nodes.append(self.node)

        return self._update_node()


    def _update_node(self):
        '''Update the parameters of the ftrack node. And Return the ftrack node
        updated
        '''

        for k, v in self.asset_info.items():
            cmd.setAttr('{}.{}'.format(self.node, k), v)

        return self.node
