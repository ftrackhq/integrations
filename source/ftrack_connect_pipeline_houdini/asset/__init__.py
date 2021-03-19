# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import json
import sys
import six

import ftrack_api

from ftrack_connect_pipeline.asset import FtrackAssetInfo, FtrackAssetBase
from ftrack_connect_pipeline_houdini.constants import asset as asset_const
from ftrack_connect_pipeline import constants as core_const
from ftrack_connect_pipeline_houdini.utils import custom_commands as houdini_utils
from ftrack_connect_pipeline_houdini.constants.asset import modes as load_const

import hou


class FtrackAssetTab(FtrackAssetBase):
    '''
    Base FtrackAssetTab class.
    '''

    def is_sync(self, obj_path):
        '''Returns bool if the current ftrack_object is sync'''
        return self._check_ftrack_object_sync(obj_path)

    def __init__(self, event_manager):
        '''
        Initialize FtrackAssetTab with *event_manager*.

        *event_manager* instance of
        :class:`ftrack_connect_pipeline.event.EventManager`
        '''
        super(FtrackAssetTab, self).__init__(event_manager)

    def init_ftrack_object(self):
        '''
        Return the ftrack ftrack_object for this class. It checks if there is
        already a matching ftrack ftrack_object in the scene, in this case it
        updates the ftrack_object if it's not. In case there is no ftrack_object
        in the scene this function creates a new one.
        '''
        obj_path = self.get_ftrack_object_path_from_scene()
        if not obj_path:
            self.logger.warning('My ftrack object has disappeared! (asset info: {})'.format(self.asset_info))
        else:
            if not self.is_sync(obj_path):
                ftrack_object = self._update_ftrack_object(obj_path)

        self.obj_path = obj_path

        return self.obj_path

    @staticmethod
    def get_parameters_dictionary(obj):
        '''
        Returns a diccionary with the keys and values of the given *obj*
        parameters
        '''
        param_dict = {}
        if obj.parmTemplateGroup().findFolder('ftrack'):
            for parm in obj.parms():
                if parm.name() in asset_const.KEYS:
                    param_dict[parm.name()] = parm.eval()
        return param_dict

    @staticmethod
    def get_ftrack_object_path_from_scene_on_asset_info(asset_info):
        ftrack_asset_nodes = houdini_utils.get_ftrack_objects()
        for obj in ftrack_asset_nodes:
            param_dict = FtrackAssetTab.get_parameters_dictionary(obj)
            # avoid read and write nodes containing the old ftrack tab
            # without information
            if not param_dict:
                continue
            node_asset_info = FtrackAssetInfo(param_dict)
            if node_asset_info.is_deprecated:
                raise DeprecationWarning(
                    "Can not read v1 ftrack asset plugin")
            if (
                    node_asset_info[asset_const.REFERENCE_OBJECT] ==
                    asset_info[asset_const.REFERENCE_OBJECT]
            ):
                return obj.path()
        return None

    def get_ftrack_object_path_from_scene(self):
        '''
        Return the ftrack object path from the current asset_version if it exists in
        the scene.
        '''
        return self.get_ftrack_object_path_from_scene_on_asset_info(self.asset_info)

    def _check_ftrack_object_sync(self, obj_path):
        '''
        Check if the current parameters of the ftrack_object match the
        values of the asset_info.
        '''
        if not obj_path:
            self.logger.warning("No object provided")
            return False

        synced = False
        obj = hou.node(obj_path)
        param_dict = self.get_parameters_dictionary(obj)
        node_asset_info = FtrackAssetInfo(param_dict)

        if node_asset_info == self.asset_info:
            self.logger.debug("{} is synced".format(ftrack_object))
            synced = True

        return synced

    def _add_ftab(self, obj):
        '''
        Add ftrack asset parameters to object.
        '''
        parm_group = obj.parmTemplateGroup()
        parm_folder = hou.FolderParmTemplate('folder', 'ftrack')
        alembic_folder = parm_group.findFolder('Alembic Loading Parameters')

        for comp in asset_const.KEYS:
            parm_folder.addParmTemplate(
                hou.StringParmTemplate(comp, comp, 1, ''))
        if alembic_folder:
            parm_group.insertAfter(alembic_folder, parm_folder)
        else:
            parm_group.append(parm_folder)
        obj.setParmTemplateGroup(parm_group)

    def _set_ftab(self, obj):
        '''
        Add ftrack asset parameters to object.
        '''

        def safeString(string):

            if six.PY2 and isinstance(string, unicode):
                return string.encode('utf-8')
            if isinstance(string, bytes):
                return string.decode("utf-8")
            return str(string)

        for k, v in self.asset_info.items():
            obj.parm(k).set(safeString(v))

    def connect_objects(self, objects):
        '''
        Add asset info to Houdini objects
        '''
        for obj in objects:
            self._add_ftab(obj)
            self._set_ftab(obj)

    def _update_ftrack_object(self, obj_path):
        '''
        Update the parameters of the ftrack_object. And Return the
        ftrack_object updated
        '''
        obj = hou.node(obj_path)
        self._set_ftab(obj)
        return obj.path()
