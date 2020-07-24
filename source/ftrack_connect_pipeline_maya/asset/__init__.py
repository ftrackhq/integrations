# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline.asset import FtrackAssetInfo, FtrackAssetBase
from ftrack_connect_pipeline_maya.constants import asset as asset_const
from ftrack_connect_pipeline_maya.utils import custom_commands as maya_utils

import maya.cmds as cmd


class FtrackAssetNode(FtrackAssetBase):
    '''
    Base FtrackAssetNode class.
    '''

    def is_sync(self, ftrack_object):
        '''Returns bool if the current ftrack_object is sync'''
        return self._check_ftrack_object_sync(ftrack_object)

    def __init__(self, event_manager):
        '''
        Initialize FtrackAssetBase with *event_manager*.

        *event_manager* instance of
        :class:`ftrack_connect_pipeline.event.EventManager`
        '''
        super(FtrackAssetNode, self).__init__(event_manager)

    def init_ftrack_object(self):
        '''
        Return the ftrack ftrack_object for this class. It checks if there is
        already a matching ftrack ftrack_object in the scene, in this case it
        updates the ftrack_object if it's not. In case there is no ftrack_object
        in the scene this function creates a new one.
        '''
        ftrack_object = self.get_ftrack_object_from_scene()
        if not ftrack_object:
            ftrack_object = self.create_new_ftrack_object()
        if ftrack_object:
            if not self.is_sync(ftrack_object):
                ftrack_object = self._update_ftrack_object(ftrack_object)

        self.ftrack_object = ftrack_object

        return self.ftrack_object

    @staticmethod
    def get_parameters_dictionary(maya_obj):
        '''
        Returns a diccionary with the keys and values of the given *maya_obj*
        parameters
        '''
        param_dict = {}
        all_attr = cmd.listAttr(maya_obj, c=True, se=True)
        for attr in all_attr:
            if cmd.attributeQuery(attr, node=maya_obj, msg=True):
                continue
            attr_value = cmd.getAttr('{}.{}'.format(maya_obj, attr))
            param_dict[attr] = attr_value
        return param_dict

    def get_ftrack_object_from_scene(self):
        '''
        Return the ftrack_object from the current asset_version if it exists in
        the scene.
        '''
        ftrack_asset_nodes = maya_utils.get_ftrack_nodes()
        for ftrack_object in ftrack_asset_nodes:
            param_dict = self.get_parameters_dictionary(ftrack_object)
            node_asset_info = FtrackAssetInfo(param_dict)
            if node_asset_info.is_deprecated:
                raise DeprecationWarning("Can not read v1 ftrack asset plugin")
            if (
                    node_asset_info[asset_const.REFERENCE_OBJECT] ==
                    self.asset_info[asset_const.REFERENCE_OBJECT]
            ):

                return ftrack_object

    def _check_ftrack_object_sync(self, ftrack_object):
        '''
        Check if the current parameters of the ftrack_object match the
        values of the asset_info.
        '''
        if not ftrack_object:
            self.logger.warning(
                "Can't check if ftrack_object is not loaded"
            )
            return False

        synced = False

        param_dict = self.get_parameters_dictionary(ftrack_object)
        node_asset_info = FtrackAssetInfo(param_dict)

        if node_asset_info == self.asset_info:
            self.logger.debug("{} is synced".format(ftrack_object))
            synced = True

        return synced

    def _get_unique_ftrack_object_name(self):
        '''
        Return a unique scene name for the current ftrack_object
        '''
        ftrack_object_name = super(
            FtrackAssetNode, self
        )._get_unique_ftrack_object_name()

        count = 0
        while 1:
            if cmd.objExists(ftrack_object_name):
                ftrack_object_name = ftrack_object_name + str(count)
                count = count + 1
            else:
                break
        return ftrack_object_name

    def connect_objects(self, objects):
        '''
        Parent the given *objects* under current ftrack_object

        *objects* is List type of INode
        '''
        for obj in objects:
            if cmd.lockNode(obj, q=True)[0]:
                cmd.lockNode(obj, l=False)

            if not cmd.attributeQuery('ftrack', n=obj, exists=True):
                cmd.addAttr(obj, ln='ftrack', at='message')

            if not cmd.listConnections('{}.ftrack'.format(obj)):
                cmd.connectAttr(
                    '{}.{}'.format(self.ftrack_object, asset_const.ASSET_LINK),
                    '{}.ftrack'.format(obj)
                )

    def get_load_mode_from_ftrack_object(self, obj):
        '''Return the import mode used to import an asset.'''
        load_mode = cmd.getAttr('{}.{}'.format(
            obj, asset_const.LOAD_MODE)
        )
        return load_mode

    def create_new_ftrack_object(self):
        '''
        Creates a ftrack_object with a unique name.
        '''

        name = self._get_unique_ftrack_object_name()
        ftrack_object = cmd.createNode('ftrackAssetNode', name=name)

        return ftrack_object

    def _update_ftrack_object(self, ftrack_object):
        '''
        Update the parameters of the ftrack_object. And Return the
        ftrack_object updated
        '''
        for k, v in self.asset_info.items():
            cmd.setAttr('{}.{}'.format(ftrack_object, k), l=False)
            if k == asset_const.VERSION_NUMBER:
                cmd.setAttr('{}.{}'.format(ftrack_object, k), v, l=True)
            elif k == asset_const.REFERENCE_OBJECT:
                cmd.setAttr(
                    '{}.{}'.format(
                        ftrack_object, k
                    ), str(ftrack_object), type="string", l=True
                )
            else:
                cmd.setAttr('{}.{}'.format(
                    ftrack_object, k), v, type="string", l=True
                )

        return ftrack_object

    # def discover_assets(self):
    #     '''
    #     Returns asset_info_list with all the assets loaded in the current
    #     scene that has an ftrack_object connected
    #     '''
    #     ftrack_asset_nodes = maya_utils.get_ftrack_nodes()
    #     asset_info_list = []
    #
    #     for ftrack_object in ftrack_asset_nodes:
    #         param_dict = self.get_parameters_dictionary(ftrack_object)
    #         node_asset_info = FtrackAssetInfo(param_dict)
    #         asset_info_list.append(node_asset_info)
    #     return asset_info_list

    # def remove_current_objects(self):
    #     '''
    #     Remove all the imported or referenced objects in the scene
    #     '''
    #     referenceNode = False
    #     for node in cmd.listConnections(
    #             '{}.{}'.format(self.ftrack_object, asset_const.ASSET_LINK)
    #     ):
    #         if cmd.nodeType(node) == 'reference':
    #             referenceNode = maya_utils.getReferenceNode(node)
    #             if referenceNode:
    #                 break
    #
    #     if referenceNode:
    #         self.logger.debug("Removing reference: {}".format(referenceNode))
    #         maya_utils.remove_reference_node(referenceNode)
    #     else:
    #         nodes = cmd.listConnections(
    #             '{}.{}'.format(self.ftrack_object, asset_const.ASSET_LINK)
    #         )
    #         for node in nodes:
    #             try:
    #                 self.logger.debug(
    #                     "Removing object: {}".format(node)
    #                 )
    #                 if cmd.objExists(node):
    #                     cmd.delete(node)
    #             except Exception as error:
    #                 self.logger.error(
    #                     'Node: {0} could not be deleted, error: {1}'.format(
    #                         node, error
    #                     )
    #                 )
    #     if cmd.objExists(self.ftrack_object):
    #         cmd.delete(self.ftrack_object)
    #
    # def _remove_asset(self, event):
    #     '''
    #     Override function from the main class, remove the current assets of the
    #     scene.
    #     '''
    #     super(FtrackAssetNode, self)._remove_asset(event)
    #
    #     asset_item = event['data']
    #
    #     try:
    #         self.logger.debug("Removing current objects")
    #         self.remove_current_objects()
    #     except Exception, e:
    #         self.logger.error("Error removing current objects: {}".format(e))
    #
    #     return asset_item

    # def _select_asset(self, event):
    #     '''
    #     Override function from the main class, select the current assets of the
    #     scene.
    #     '''
    #     super(FtrackAssetNode, self)._select_asset(event)
    #     asset_item = event['data']
    #
    #     nodes = cmd.listConnections(
    #         '{}.{}'.format(self.ftrack_object, asset_const.ASSET_LINK)
    #     )
    #     for node in nodes:
    #         cmd.select(node, add=True)
    #
    #     return asset_item

