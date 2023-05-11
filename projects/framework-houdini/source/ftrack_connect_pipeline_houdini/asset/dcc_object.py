# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import six

import logging
from ftrack_connect_pipeline.asset.dcc_object import DccObject
from ftrack_connect_pipeline import utils as core_utils
from ftrack_connect_pipeline_houdini.constants import asset as asset_const
from ftrack_connect_pipeline_houdini import utils as houdini_utils

import hou


class HoudiniDccObject(DccObject):
    '''HoudiniDccObject class.'''

    def __init__(self, name=None, from_id=None, **kwargs):
        '''
        If the *from_id* is provided find an object in the dcc with the given
        *from_id* as assset_info_id.
        If a *name* is provided create a new object in the dcc.
        '''
        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )
        super(HoudiniDccObject, self).__init__(name, from_id, **kwargs)

    def create(self, name):
        '''
        Creates a new node with the given *name* if doesn't exists.
        '''
        node_path = '/obj/{}'.format(name)
        if self._name_exists(node_path):
            error_message = "{} already exists in the scene".format(name)
            self.logger.error(error_message)
            raise RuntimeError(error_message)

        root = hou.node('/obj')
        ftrack_node = root.createNode('null')
        ftrack_node.setName(name)
        ftrack_node.hide(True)
        ftrack_node.setDisplayFlag(False)
        self.logger.debug('Creating new dcc object {}'.format(ftrack_node))
        self._add_ftab(ftrack_node)
        self.name = ftrack_node.path()
        return self.name

    @staticmethod
    def _add_ftab(node, keys=None):
        '''
        Add ftrack asset parameters to object.
        '''
        if keys is None:
            keys = asset_const.KEYS
        parm_group = node.parmTemplateGroup()
        parm_folder = hou.FolderParmTemplate('folder', 'ftrack')
        alembic_folder = parm_group.findFolder('Alembic Loading Parameters')

        for key in keys:
            parm_folder.addParmTemplate(
                hou.StringParmTemplate(key, key, 1, '')
            )
        if alembic_folder:
            parm_group.insertAfter(alembic_folder, parm_folder)
        else:
            parm_group.append(parm_folder)
        node.setParmTemplateGroup(parm_group)

    def _name_exists(self, name):
        '''
        Return true if the given *name* exists in the scene.
        '''
        if hou.node(name):
            return True

        return False

    def __setitem__(self, k, v):
        '''
        Sets the given *v* into the given *k* and automatically set the
        attributes of the current self :obj:`name` on the DCC
        '''
        ftrack_node = hou.node(self.name)

        if not ftrack_node:
            raise Exception(
                'ftrack node "{}" does not exists'.format(self.name)
            )

        if k == asset_const.REFERENCE_OBJECT:
            ftrack_node.parm(k).set(
                core_utils.safe_string(str(ftrack_node.name()))
            )
        elif k == asset_const.DEPENDENCY_IDS:
            ftrack_node.parm(k).set(core_utils.safe_string(','.join(v or [])))
        else:
            ftrack_node.parm(k).set(core_utils.safe_string(v))

        super(HoudiniDccObject, self).__setitem__(k, v)

    def from_asset_info_id(self, asset_info_id):
        '''
        Checks houdini scene to get all the ftrackAssetNode objects. Compares them
        with the given *asset_info_id* and returns them if matches.
        '''
        for node in houdini_utils.get_ftrack_nodes(as_node=True):
            id_value = node.parm(asset_const.ASSET_INFO_ID).eval()
            if id_value == asset_info_id:
                self.logger.debug(
                    'Found existing object: {}'.format(node.name())
                )
                self.name = node.path()
                return self.name

        self.logger.debug(
            "Couldn't found an existing object for the asset info id: {}".format(
                asset_info_id
            )
        )
        return None

    @staticmethod
    def dictionary_from_object(object_name):
        '''
        Static method to be used without initializing the current class.
        Returns a dictionary with the keys and values of the given
        *object_name* if exists.

        *object_name* ftrackAssetNode object type from houdini scene.
        '''
        logger = logging.getLogger(
            '{0}.{1}'.format(__name__, __class__.__name__)
        )
        param_dict = {}
        if not hou.node(object_name):
            error_message = "{} Object doesn't exists".format(object_name)
            logger.error(error_message)
            return param_dict
        ftrack_node = hou.node(object_name)
        if ftrack_node.parmTemplateGroup().findFolder('ftrack'):
            for parm in ftrack_node.parms():
                if parm.name() in asset_const.KEYS:
                    value = parm.eval()
                    if parm.name() == asset_const.DEPENDENCY_IDS:
                        value = []
                        if len(value) > 0:
                            value = value.split(',')
                    param_dict[parm.name()] = value
        return param_dict

    def connect_objects(self, objects):
        '''
        Add the asset_info_id of the self :obj:`name` object to *objects* asset_link
        attribute, creating a link that way as no means of connecting parameters exists
        in Houdini.

        *objects* List of Houdini Node objects
        '''
        ftrack_node = hou.node(self.name)
        for node in objects:
            if node != ftrack_node:
                self._add_ftab(node, keys=[asset_const.ASSET_LINK])
                node.parm(asset_const.ASSET_LINK).set(self.name)
