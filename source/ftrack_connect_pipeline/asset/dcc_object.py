# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import logging
import ftrack_api
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo
from ftrack_connect_pipeline.constants import asset as asset_const
from ftrack_connect_pipeline import constants

# TODO: think about inherit from dictionary and our conform data method is the
#  parameters dictionary.
class DccObject(dict):
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

    # def _conform_data(self, mapping):
    #     '''
    #     Creates the FtrackAssetInfo object from the given dictionary on the
    #     *mapping* argument
    #     '''
    #     new_mapping = {}
    #     for k in mapping.keys():
    #         v = mapping.get(k)
    #         # Sometimes the value None is interpreted as unicode (in maya
    #         # mostly) we are converting to a type None
    #         if v == u'None':
    #             v = None
    #         new_mapping.setdefault(k, v)
    #
    #     return new_mapping

    #TODO: we may want to create an object with the given asset info, but then
    # we have to make sure that we automatically setAttr in the application too
    def __init__(self, name=None, from_id=None, **kwargs):
        '''
        Initialize FtrackAssetBase with instance of
        :class:`~ftrack_connect_pipeline.event.EventManager`
        '''
        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )
        # asset_info = asset_info or {}
        if from_id:
            self.from_asset_info_id(from_id)
        elif name:
            self.create(name)
        # mapping = self._conform_data(asset_info)
        super(DccObject, self).__init__({}, **kwargs)

    def __getitem__(self, k):
        '''
        Get the value from the given *k*

        Note:: In case of the given *k* is the asset_info_options it will
        automatically return the decoded json.
        '''

        value = super(DccObject, self).__getitem__(k)
        return value

    def __setitem__(self, k, v):
        '''
        Sets the given *v* into the given *k*

        Note:: In case of the given *k* is the asset_info_options it will
        automatically encode the given json value to base64
        '''
        super(DccObject, self).__setitem__(k, v)

    def get(self, k, default=None):
        '''
        If exists, returns the value of the given *k* otherwise returns
        *default*.

        *k* : Key of the current dictionary.

        *default* : Default value of the given Key.
        '''
        value = super(DccObject, self).get(k, default)
        return value

    def update(self, *args, **kwargs):
        if args:
            if len(args) > 1:
                raise TypeError("update expected at most 1 arguments, "
                                "got %d" % len(args))
            other = dict(args[0])
            for key in other:
                self[key] = other[key]
        for key in kwargs:
            self[key] = kwargs[key]

    def setdefault(self, key, value=None):
        if key not in self:
            self[key] = value
        return self[key]

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

    def from_asset_info_id(self, asset_info_id):
        '''
        Checks maya scene to get all the FtrackAssetNode objects. Compares them
        with the current self :obj:`asset_info` and returns it if the asset_info_id
        matches.
        '''
        raise NotImplementedError

    @staticmethod
    def dictionary_from_object(object_name):
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