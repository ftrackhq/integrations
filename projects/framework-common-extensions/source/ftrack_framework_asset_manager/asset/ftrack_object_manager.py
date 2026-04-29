# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
import unicodedata
import re

from ftrack_framework_asset_manager.asset.ftrack_asset_info import (
    FtrackAssetInfo,
)
from ftrack_framework_asset_manager.asset.dcc_object import DccObject
from ftrack_framework_asset_manager.asset import constants


class FtrackObjectManager(object):
    DccObject = DccObject

    @property
    def asset_info(self):
        return self._asset_info

    @asset_info.setter
    def asset_info(self, value):
        if not isinstance(value, FtrackAssetInfo):
            try:
                value = FtrackAssetInfo(value)
            except Exception:
                raise ValueError(
                    'Could not initialise asset info from {}!'.format(value)
                )
        self._asset_info = value

    @property
    def dcc_object(self):
        return self._dcc_object

    @dcc_object.setter
    def dcc_object(self, value):
        if not isinstance(value, self.DccObject):
            raise ValueError('DccObject {} should be instance of DccObject')
        if not self._check_sync(value):
            self._sync(value)
        self._dcc_object = value

    @property
    def session(self):
        return self._session

    @property
    def is_sync(self):
        return self._check_sync(self.dcc_object)

    @property
    def objects_loaded(self):
        return self.asset_info[constants.OBJECTS_LOADED]

    @objects_loaded.setter
    def objects_loaded(self, value):
        self.asset_info[constants.OBJECTS_LOADED] = value
        if self.dcc_object:
            self.dcc_object.objects_loaded = value

    def __init__(self, session, event_manager=None):
        super(FtrackObjectManager, self).__init__()
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self._asset_info = None
        self._dcc_object = None
        self._session = session
        self._event_manager = event_manager

    def generate_dcc_object_name(self):
        short_id = "{}{}".format(
            self.asset_info[constants.ASSET_INFO_ID][:2],
            self.asset_info[constants.ASSET_INFO_ID][-2:],
        )
        name_value = self.asset_info[constants.CONTEXT_PATH]
        name_value = unicodedata.normalize('NFKD', str(name_value)).encode(
            'ascii', 'ignore'
        )
        name_value = re.sub('[^\w\.-]', "_", name_value.decode('utf-8'))

        dcc_object_name = constants.DCC_OBJECT_NAME.format(
            name_value,
            short_id,
        )

        return str(dcc_object_name.strip().lower())

    def _check_sync(self, dcc_object):
        if not isinstance(dcc_object, self.DccObject):
            raise ValueError('DccObject {} should be instance of DccObject')
        synced = False
        node_asset_info = FtrackAssetInfo(dcc_object)
        if node_asset_info == self.asset_info:
            self.logger.debug("{} is synced".format(dcc_object.name))
            synced = True
        return synced

    def _sync(self, dcc_object):
        dcc_object.update(self.asset_info)

    def connect_objects(self, objects):
        self.dcc_object.connect_objects(objects)

    def create_new_dcc_object(self):
        name = self.generate_dcc_object_name()
        dcc_object = self.DccObject(name)
        self.dcc_object = dcc_object
        return self.dcc_object
