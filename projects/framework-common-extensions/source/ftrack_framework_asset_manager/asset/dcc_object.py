# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging

from ftrack_framework_asset_manager.asset import constants


class DccObject(dict):
    ftrack_plugin_id = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def objects_loaded(self):
        return self[constants.OBJECTS_LOADED]

    @objects_loaded.setter
    def objects_loaded(self, value):
        self[constants.OBJECTS_LOADED] = value

    def __init__(self, name=None, from_id=None, **kwargs):
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
        return super(DccObject, self).__getitem__(k)

    def __setitem__(self, k, v):
        super(DccObject, self).__setitem__(k, v)

    def get(self, k, default=None):
        return super(DccObject, self).get(k, default)

    def update(self, *args, **kwargs):
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
        if key not in self:
            self[key] = value
        return self[key]

    def create(self, name):
        raise NotImplementedError

    def _name_exists(self, name):
        raise NotImplementedError

    def from_asset_info_id(self, asset_info_id):
        raise NotImplementedError

    @staticmethod
    def dictionary_from_object(object_name):
        raise NotImplementedError

    def connect_objects(self, objects):
        raise NotImplementedError
