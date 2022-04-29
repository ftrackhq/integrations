# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import logging
import ftrack_api
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo
from ftrack_connect_pipeline.constants import asset as asset_const
from ftrack_connect_pipeline import constants

# TODO: think about inherit from dictionary and our conform data method is the
#  parameters dictionary.
class DccObject(object):
    '''Base DccObject class.'''

    ftrack_plugin_id = None
    '''Plugin id used on some DCC applications '''

    @property
    def name(self):
        '''
        Return name of the object
        '''
        return self._name

    @name.setter
    def name(self, value):
        '''
        Sets name of the object
        '''
        self._name = value

    def __init__(self, name=None):
        '''
        Initialize FtrackAssetBase with instance of
        :class:`~ftrack_connect_pipeline.event.EventManager`
        '''
        super(DccObject, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        if name and self._name_exists(name):
            self.name = name

    def create(self, name):
        '''
        Creates a new dcc_object with a unique name.
        '''
        raise NotImplementedError

    def _name_exists(self, name):
        '''
        Return a scene name for the current self :obj:`dcc_object`.
        '''
        raise NotImplementedError

    def update(self, asset_info):
        '''
        Updates the parameters of the given *dcc_object* based on the
        self :obj:`asset_info`.
        '''
        raise NotImplementedError

    def from_asset_info_id(self, asset_info_id):
        '''
        Checks maya scene to get all the FtrackAssetNode objects. Compares them
        with the current self :obj:`asset_info` and returns it if the asset_info_id
        matches.
        '''
        raise NotImplementedError

    def parameters_dictionary(self, object_name):
        '''
        Static method to be used without initializing the current class.
        Returns a dictionary with the keys and values of the given
        *maya_ftrack_obj* if exists.

        *maya_ftrack_obj* FtrackAssetNode object type from maya scene.
        '''
        raise NotImplementedError

    def connect_objects(self, objects):
        '''
        Link the given *objects* ftrack attribute to the self
        :obj:`dcc_object` asset_link attribute in maya.

        *objects* List of Maya DAG objects
        '''
        raise NotImplementedError