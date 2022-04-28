# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import logging
import ftrack_api
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo
from ftrack_connect_pipeline.constants import asset as asset_const
from ftrack_connect_pipeline import constants


class FtrackObjectManager(object):
    '''Base FtrackAssetBase class.'''

    @property
    def asset_info(self):
        '''
        Returns instance of
        :class:`~ftrack_connect_pipeline.asset.FtrackAssetInfo`
        '''
        return self._asset_info

    @asset_info.setter
    def asset_info(self, value):
        '''
        Sets the self.asset_info,
        *value* :class:`~ftrack_connect_pipeline.asset.FtrackAssetInfo`
        '''
        if not isinstance(value, FtrackAssetInfo):
            try:
                value = FtrackAssetInfo(value)
            except Exception:
                raise ValueError(
                    'Could not initialise asset info from {}!'.format(value)
                )

        self._asset_info = value

    @property
    def session(self):
        '''
        Returns instance of :class:`ftrack_api.session.Session`
        '''
        return self.event_manager.session

    @property
    def event_manager(self):
        '''Returns instance of
        :class:`~ftrack_connect_pipeline.event.EventManager`'''
        return self._event_manager

    @property
    def is_sync(self):
        return self._check_sync()

    @property
    def dcc_object(self):
        '''
        Returns the current dcc_object
        '''
        return self._dcc_object

    @dcc_object.setter
    def dcc_object(self, value):
        '''Sets the current dcc_object'''
        self._dcc_object = value
        if not self.is_sync:
            self.sync()

    @property
    def objects_loaded(self):
        '''
        Returns If the asset is loaded
        '''
        return self.asset_info[asset_const.OBJECTS_LOADED]

    @objects_loaded.setter
    def objects_loaded(self, value):
        '''
        Set the self :obj:`asset_info` as loaded.

        *loaded* True if the objects are loaded in the scene.
        '''
        self.asset_info[asset_const.OBJECTS_LOADED] = value

    def __init__(self, event_manager):
        '''
        Initialize FtrackAssetBase with instance of
        :class:`~ftrack_connect_pipeline.event.EventManager`
        '''
        super(FtrackObjectManager, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self._asset_info = None
        self._dcc_object = None
        self._event_manager = event_manager

    def _generate_dcc_object_name(self):
        '''
        Returns a name for the current self :obj:`dcc_object` based on
        the first 2 and last 2 characters of the
        :constant:`asset_const.ASSET_INFO_ID`
        '''
        short_id = "{}{}".format(
            self.asset_info[asset_const.ASSET_INFO_ID][:2],
            self.asset_info[asset_const.ASSET_INFO_ID][-2:],
        )
        dcc_object_name = asset_const.DCC_OBJECT_NAME.format(
            self.asset_info[asset_const.CONTEXT_PATH].replace(":", "_"),
            short_id,
        )
        return dcc_object_name

    def _check_sync(self):
        '''
        Check if the parameters of the given *dcc_object* match the
        values of the current self :obj:`asset_info`.
        '''
        raise NotImplementedError

    def sync(self):
        '''
        Updates the parameters of the given *dcc_object* based on the
        self :obj:`asset_info`.
        '''
        raise NotImplementedError

    def connect_objects(self, objects):
        '''
        Link the given *objects* ftrack attribute to the self
        :obj:`dcc_object` asset_link attribute in maya.

        *objects* List of Maya DAG objects
        '''
        raise NotImplementedError

    def create_new_dcc_object(self):
        '''
        Creates a new dcc_object with a unique name.
        '''
        raise NotImplementedError