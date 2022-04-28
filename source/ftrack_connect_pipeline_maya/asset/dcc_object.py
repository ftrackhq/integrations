# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import logging
from ftrack_connect_pipeline.asset.dcc_object import DccObject
from ftrack_connect_pipeline_maya.constants import asset as asset_const
from ftrack_connect_pipeline_maya.utils import custom_commands as maya_utils

import maya.cmds as cmds

class MayaDccObject(DccObject):
    '''MayaDccObject class.'''

    ftrack_plugin_id = asset_const.FTRACK_PLUGIN_ID
    '''Plugin id used on some DCC applications '''


    @property
    def objects_loaded(self):
        '''
        Returns If the asset is loaded
        '''
        return cmds.getAttr('{}.{}'.format(self.name, asset_const.OBJECTS_LOADED))

    @objects_loaded.setter
    def objects_loaded(self, value):
        '''
        Set dcc object loaded parameter to *value*.

        *loaded* True if the objects are loaded in the scene.
        '''
        # Update and sync the dcc_object asset_info with the
        # self.asset_info
        cmds.setAttr(
            '{}.{}'.format(self.name, asset_const.OBJECTS_LOADED),
            l=False,
        )
        cmds.setAttr(
            '{}.{}'.format(self.name, asset_const.OBJECTS_LOADED),
            value,
            type="string",
            l=True,
        )

    def __init__(self, name=None):
        '''
        Initialize FtrackAssetBase with instance of
        :class:`~ftrack_connect_pipeline.event.EventManager`
        '''
        super(MayaDccObject, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        if name and self._name_exists(name):
            self.name = name

    def create(self, name):
        '''
        Creates a new dcc_object with a unique name.
        '''
        if self._name_exists(name):
            error_message = "{} already exists in the scene".format(name)
            self.logger.error(error_message)
            raise RuntimeError(error_message)

        # TODO: replace ftrackAssetNode for a constant name
        dcc_object = cmds.createNode('ftrackAssetNode', name=name)
        self.logger.debug(
            'Creating new dcc object {}'.format(dcc_object)
        )
        self.name = dcc_object
        return self.name

    def _name_exists(self, name):
        '''
        Return a scene name for the current self :obj:`dcc_object`.
        '''
        if cmds.objExists(name):
            return True

        return False

    def update(self, asset_info):
        '''
        Updates the parameters of the given *dcc_object* based on the
        self :obj:`asset_info`.
        '''
        for k, v in list(asset_info.items()):
            cmds.setAttr('{}.{}'.format(self.name, k), l=False)
            if k == asset_const.VERSION_NUMBER:
                cmds.setAttr('{}.{}'.format(self.name, k), v, l=True)
            elif k == asset_const.REFERENCE_OBJECT:
                cmds.setAttr(
                    '{}.{}'.format(self.name, k),
                    str(self.name),
                    type="string",
                    l=True,
                )
            elif k == asset_const.IS_LATEST_VERSION:
                cmds.setAttr('{}.{}'.format(self.name, k), bool(v), l=True)

            elif k == asset_const.DEPENDENCY_IDS:
                cmds.setAttr(
                    '{}.{}'.format(self.name, k),
                    *([len(v)] + v),
                    type="stringArray",
                    l=True
                )

            else:
                cmds.setAttr(
                    '{}.{}'.format(self.name, k), v, type="string", l=True
                )

    def from_asset_info_id(self, asset_info_id):
        '''
        Checks maya scene to get all the FtrackAssetNode objects. Compares them
        with the current self :obj:`asset_info` and returns it if the asset_info_id
        matches.
        '''
        ftrack_asset_nodes = maya_utils.get_ftrack_nodes()
        for dcc_object_name in ftrack_asset_nodes:
            param_dict = self.parameters_dictionary(dcc_object_name)
            if (
                    param_dict[asset_const.ASSET_INFO_ID]
                    == asset_info_id
            ):
                self.logger.debug(
                    'Found existing object: {}'.format(dcc_object_name)
                )
                self.name = dcc_object_name
                return self.name

        self.logger.debug(
            "Couldn't found anexisting object for the asset info id: {}".format(
                asset_info_id
            )
        )
        return None

    def parameters_dictionary(self, object_name):
        '''
        Static method to be used without initializing the current class.
        Returns a dictionary with the keys and values of the given
        *maya_ftrack_obj* if exists.

        *maya_ftrack_obj* FtrackAssetNode object type from maya scene.
        '''
        if not object_name:
            object_name = self.name
        param_dict = {}
        if not cmds.objExists(object_name):
            error_message = "{} Object doesn't exists".format(object_name)
            self.logger.error(error_message)
            return param_dict
        all_attr = cmds.listAttr(object_name, c=True, se=True)
        for attr in all_attr:
            if cmds.attributeQuery(attr, node=object_name, msg=True):
                continue
            attr_value = cmds.getAttr('{}.{}'.format(object_name, attr))
            param_dict[attr] = attr_value
        return param_dict

    def connect_objects(self, objects):
        '''
        Link the given *objects* ftrack attribute to the self
        :obj:`dcc_object` asset_link attribute in maya.

        *objects* List of Maya DAG objects
        '''
        for obj in objects:
            if cmds.lockNode(obj, q=True)[0]:
                cmds.lockNode(obj, l=False)

            if not cmds.attributeQuery('ftrack', n=obj, exists=True):
                cmds.addAttr(obj, ln='ftrack', at='message')

            if not cmds.listConnections('{}.ftrack'.format(obj)):
                cmds.connectAttr(
                    '{}.{}'.format(self.name, asset_const.ASSET_LINK),
                    '{}.ftrack'.format(obj),
                )