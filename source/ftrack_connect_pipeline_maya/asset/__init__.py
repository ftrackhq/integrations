# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline.asset import FtrackAssetInfo, FtrackAssetBase
from ftrack_connect_pipeline_maya.constants import asset as asset_const
from ftrack_connect_pipeline_maya.utils import custom_commands as maya_utils

import maya.cmds as cmds
import logging


class FtrackAssetNode(FtrackAssetBase):
    '''
    Base class to manage FtrackAssetNode object in the maya scene.
    '''

    ftrack_plugin_id = asset_const.FTRACK_PLUGIN_ID

    def __init__(self, event_manager):
        '''
        Initialize FtrackAssetNode with *event_manager*.

        *event_manager* instance of
        :class:`ftrack_connect_pipeline.event.EventManager`
        '''
        super(FtrackAssetNode, self).__init__(event_manager)

    def init_ftrack_object(self, create_object=True):
        '''
        Returns the self :obj:`ftrack_object`.
        if the given *create_object* argument is set to True, creates a new
        :obj:`ftrack_object` with the self :obj:`asset_info` options on it.
        Otherwise, if the given *create_object* is set to False a matching
        :obj:`ftrack_object` will be found on the current scene based on the
        self :obj:`asset_info`.

        *create_object* If true creates a new ftrack object
        *is_loaded* Means that the objects are loaded in the scene, If true
        tags :obj:`asset_info` as loaded.
        '''
        ftrack_object = (
            self.create_new_ftrack_object()
            if create_object
            else self.get_ftrack_object_from_scene()
        )

        if not ftrack_object:
            return None

        if not self.is_sync(ftrack_object):
            ftrack_object = self._update_ftrack_object(ftrack_object)

        self.ftrack_object = ftrack_object

        return self.ftrack_object

    def is_sync(self, ftrack_object):
        '''
        Returns bool if the current :obj:`asset_info` of the given
        *ftrack_object* is sync with the self :obj:`asset_info`
        '''
        return self._check_ftrack_object_sync(ftrack_object)

    def set_loaded(self, loaded):
        '''
        Set the self :obj:`asset_info` as loaded and update the attributes in
        the current self :obj:`ftrack_object` if exists.

        *loaded* True if the objects are loaded in the scene.
        '''
        self.asset_info[asset_const.IS_LOADED] = loaded
        if self.ftrack_object:
            # Update and sync the ftrack_object asset_info with the
            # self.asset_info
            cmds.setAttr(
                '{}.{}'.format(self.ftrack_object, asset_const.IS_LOADED),
                l=False,
            )
            cmds.setAttr(
                '{}.{}'.format(self.ftrack_object, asset_const.IS_LOADED),
                self.asset_info[asset_const.IS_LOADED],
                type="string",
                l=True,
            )

    @staticmethod
    def get_dictionary_from_ftrack_object(maya_ftrack_obj):
        '''
        Static method to be used without initializing the current class.
        Returns a dictionary with the keys and values of the given
        *maya_ftrack_obj* if exists.

        *maya_ftrack_obj* FtrackAssetNode object type from maya scene.
        '''
        logger = logging.getLogger(__name__ + '.' + __class__.__name__)
        param_dict = {}
        if not cmds.objExists(maya_ftrack_obj):
            error_message = "{} Object doesn't exists".format(maya_ftrack_obj)
            logger.error(error_message)
            return param_dict
        all_attr = cmds.listAttr(maya_ftrack_obj, c=True, se=True)
        for attr in all_attr:
            if cmds.attributeQuery(attr, node=maya_ftrack_obj, msg=True):
                continue
            attr_value = cmds.getAttr('{}.{}'.format(maya_ftrack_obj, attr))
            param_dict[attr] = attr_value
        return param_dict

    def get_ftrack_object_from_scene(self):
        '''
        Checks maya scene to get all the FtrackAssetNode objects. Compares them
        with the current self :obj:`asset_info` and returns it if the asset_info_id
        matches.
        '''
        ftrack_asset_nodes = maya_utils.get_ftrack_nodes()
        for ftrack_object in ftrack_asset_nodes:
            param_dict = self.get_dictionary_from_ftrack_object(ftrack_object)
            node_asset_info = FtrackAssetInfo(param_dict)
            if (
                node_asset_info[asset_const.ASSET_INFO_ID]
                == self.asset_info[asset_const.ASSET_INFO_ID]
            ):
                self.logger.debug(
                    'Found existing object: {}'.format(ftrack_object)
                )
                return ftrack_object

        self.logger.debug(
            "Couldn't found anexisting object for the asset info id: {}".format(
                self.asset_info[asset_const.ASSET_INFO_ID]
            )
        )
        return None

    def _check_ftrack_object_sync(self, ftrack_object):
        '''
        Check if the parameters of the given *ftrack_object* match the
        values of the current self :obj:`asset_info`.
        '''
        if not ftrack_object:
            self.logger.error("Can't check if ftrack_object is not loaded")
            return False

        synced = False

        param_dict = self.get_dictionary_from_ftrack_object(ftrack_object)
        node_asset_info = FtrackAssetInfo(param_dict)

        if node_asset_info == self.asset_info:
            self.logger.debug("{} is synced".format(ftrack_object))
            synced = True

        return synced

    def connect_objects(self, objects):
        '''
        Link the given *objects* ftrack attribute to the self
        :obj:`ftrack_object` asset_link attribute in maya.

        *objects* List of Maya DAG objects
        '''
        for obj in objects:
            if cmds.lockNode(obj, q=True)[0]:
                cmds.lockNode(obj, l=False)

            if not cmds.attributeQuery('ftrack', n=obj, exists=True):
                cmds.addAttr(obj, ln='ftrack', at='message')

            if not cmds.listConnections('{}.ftrack'.format(obj)):
                cmds.connectAttr(
                    '{}.{}'.format(self.ftrack_object, asset_const.ASSET_LINK),
                    '{}.ftrack'.format(obj),
                )

    def _generate_ftrack_object_name(self):
        '''
        Return a scene name for the current self :obj:`ftrack_object`.
        '''
        ftrack_object_name = super(
            FtrackAssetNode, self
        )._generate_ftrack_object_name()

        if cmds.objExists(ftrack_object_name):
            error_message = "{} already exists in the scene".format(
                ftrack_object_name
            )
            self.logger.error(error_message)
            raise RuntimeError(error_message)

        return ftrack_object_name

    def create_new_ftrack_object(self):
        '''
        Creates a new ftrack_object with a unique name.
        '''

        name = self._generate_ftrack_object_name()
        ftrack_object = cmds.createNode('ftrackAssetNode', name=name)
        self.logger.debug(
            'Creating new ftrack object {}'.format(ftrack_object)
        )
        return ftrack_object

    def _update_ftrack_object(self, ftrack_object):
        '''
        Updates the parameters of the given *ftrack_object* based on the
        self :obj:`asset_info`.
        '''
        for k, v in list(self.asset_info.items()):
            cmds.setAttr('{}.{}'.format(ftrack_object, k), l=False)
            if k == asset_const.VERSION_NUMBER:
                cmds.setAttr('{}.{}'.format(ftrack_object, k), v, l=True)
            elif k == asset_const.REFERENCE_OBJECT:
                cmds.setAttr(
                    '{}.{}'.format(ftrack_object, k),
                    str(ftrack_object),
                    type="string",
                    l=True,
                )
            elif k == asset_const.IS_LATEST_VERSION:
                cmds.setAttr('{}.{}'.format(ftrack_object, k), bool(v), l=True)

            elif k == asset_const.DEPENDENCY_IDS:
                cmds.setAttr(
                    '{}.{}'.format(ftrack_object, k),
                    *([len(v)] + v),
                    type="stringArray",
                    l=True
                )

            else:
                cmds.setAttr(
                    '{}.{}'.format(ftrack_object, k), v, type="string", l=True
                )

        return ftrack_object
