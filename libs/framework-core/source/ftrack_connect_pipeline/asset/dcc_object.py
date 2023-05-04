# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import logging
from ftrack_connect_pipeline.constants import asset as asset_const


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

    @property
    def objects_loaded(self):
        '''
        Returns the attribute objects_loaded of the current
        self :obj:`name`
        '''
        return self[asset_const.OBJECTS_LOADED]

    @objects_loaded.setter
    def objects_loaded(self, value):
        '''
        Set the objects_loaded attribute of the self :obj:`name` to the
        given *value*.
        '''
        self[asset_const.OBJECTS_LOADED] = value

    def __init__(self, name=None, from_id=None, **kwargs):
        '''
        If the *from_id* is provided find an object in the dcc with the given
        *from_id* as asset_info_id.
        If a *name* is provided create a new object in the dcc.
        '''
        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )
        self._name = None
        if from_id:
            self.from_asset_info_id(from_id)
        elif name:
            self.create(name)
        super(DccObject, self).__init__({}, **kwargs)

    def __getitem__(self, k):
        '''
        Get the value from the given *k*
        '''

        value = super(DccObject, self).__getitem__(k)
        return value

    def __setitem__(self, k, v):
        '''
        Sets the given *v* into the given *k*
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
        '''
        Updates the current keys and values with the given ones.
        '''
        # We override this method to make sure that we the values are updated
        # using the __setitem__ method
        if args:
            if len(args) > 1:
                raise TypeError(
                    "update expected at most 1 arguments, "
                    "got %d" % len(args)
                )
            other = dict(args[0])
            for key in other:
                self[key] = other[key]
        for key in kwargs:
            self[key] = kwargs[key]

    def setdefault(self, key, value=None):
        '''
        Sets a default value for the given key.
        '''
        if key not in self:
            self[key] = value
        return self[key]

    def create(self, name):
        '''
        Creates a new dcc_object with the given name.
        '''
        raise NotImplementedError

    def _name_exists(self, name):
        '''
        Return true if the given *name* exists in the scene.
        '''
        raise NotImplementedError

    def from_asset_info_id(self, asset_info_id):
        '''
        Checks the dcc to get all the ftrack objects. Compares them
        with the given *asset_info_id* and returns them if matches.
        '''
        raise NotImplementedError

    @staticmethod
    def dictionary_from_object(object_name):
        '''
        Static method to be used without initializing the current class.
        Returns a dictionary with the keys and values of the given
        *object_name* if exists.

        *object_name* ftrack object type from the DCC.
        '''
        raise NotImplementedError

    def connect_objects(self, objects):
        '''
        Link the given *objects* ftrack attribute to the self
        :obj:`name` object asset_link attribute in the DCC.

        *objects* List of DCC objects
        '''
        raise NotImplementedError
