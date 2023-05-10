# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging
import os
import json

import unreal

from ftrack_connect_pipeline.asset.dcc_object import DccObject

import ftrack_connect_pipeline_unreal.constants as unreal_constants
from ftrack_connect_pipeline_unreal.constants import asset as asset_const
from ftrack_connect_pipeline_unreal import utils as unreal_utils


class UnrealDccObject(DccObject):
    '''UnrealDccObject class.'''

    ftrack_plugin_id = None  # asset_const.FTRACK_PLUGIN_ID
    '''Plugin id used on some DCC applications '''

    @property
    def ftrack_file_path(self):
        '''
        Return the json file path of the current dcc object.
        '''
        # This property is added for convenience in this DCC only.
        return os.path.join(
            unreal_constants.FTRACK_ROOT_PATH, "{}.json".format(self.name)
        )

    def __init__(self, name=None, from_id=None, **kwargs):
        '''
        If the *from_id* is provided find an object in the dcc with the given
        *from_id* as assset_info_id.
        If a *name* is provided create a new object in the dcc.
        '''
        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )
        super(UnrealDccObject, self).__init__(name, from_id, **kwargs)

    def __setitem__(self, k, v):
        '''
        Sets the given *v* into the given *k* and automatically set the
        attributes of the current self :obj:`name` on the DCC
        '''
        super(UnrealDccObject, self).__setitem__(k, v)
        # As we are using a json file to handle the asset info, just dump the
        # self dictionary to the json file
        with open(self.ftrack_file_path, "w") as outfile:
            json.dump(self, outfile)

    def create(self, name):
        '''
        Creates a new dcc_object with the given *name* if doesn't exists.
        '''
        if self._name_exists(name):
            error_message = "{} already exists in the scene".format(name)
            self.logger.error(error_message)
            raise RuntimeError(error_message)

        # Set the name before creating the object because the ftrack_file_path
        # property needs the name
        self.name = name

        if not os.path.exists(unreal_constants.FTRACK_ROOT_PATH):
            self.logger.warning(
                'Creating project ftrack folder: {}'.format(
                    unreal_constants.FTRACK_ROOT_PATH
                )
            )
            os.makedirs(unreal_constants.FTRACK_ROOT_PATH)

        # Create an empty json file in the unreal project ftrack root folder
        with open(self.ftrack_file_path, "w") as outfile:
            json.dump({}, outfile)

        self.logger.debug('Creating new dcc object {}'.format(name))

        return self.name

    def exists(self):
        return self._name_exists(self.name)

    def _name_exists(self, name):
        '''
        Return true if the given *name* as ftrack file exists in the project.
        '''
        ftrack_file_path = os.path.join(
            unreal_constants.FTRACK_ROOT_PATH, "{}.json".format(name)
        )
        return unreal.Paths.file_exists(ftrack_file_path)

    def from_asset_info_id(self, asset_info_id):
        '''
        Checks unreal project to get all the ftrackAssetNode objects. Compares them
        with the given *asset_info_id* and returns them if matches.
        '''
        ftrack_asset_nodes = unreal_utils.get_ftrack_nodes()
        for dcc_object_name in ftrack_asset_nodes:
            ftrack_file_path = os.path.join(
                unreal_constants.FTRACK_ROOT_PATH,
                "{}.json".format(dcc_object_name),
            )
            param_dict = {}
            with open(ftrack_file_path, 'r') as openfile:
                param_dict = json.load(openfile)

            if param_dict.get(asset_const.ASSET_INFO_ID) == asset_info_id:
                self.logger.debug(
                    'Found existing object: {}'.format(dcc_object_name)
                )
                self.name = dcc_object_name
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

        *object_name* ftrackAssetNode object type from unreal scene.
        '''
        logger = logging.getLogger(
            '{0}.{1}'.format(__name__, __class__.__name__)
        )
        param_dict = {}
        ftrack_file_path = os.path.join(
            unreal_constants.FTRACK_ROOT_PATH, "{}.json".format(object_name)
        )
        if not unreal.Paths.file_exists(ftrack_file_path):
            error_message = "{} Object doesn't exists".format(object_name)
            logger.error(error_message)
            return param_dict

        with open(ftrack_file_path, 'r') as openfile:
            param_dict = json.load(openfile)

        return param_dict

    def connect_objects(self, objects):
        '''
        Link the given *objects* (list/set of string paths) ftrack attribute to the self
        :obj:`name` object asset_link attribute in unreal.

        *objects* List of Unreal asset paths
        '''

        for node_name in objects:
            unreal_utils.connect_object(node_name, self, self.logger)
