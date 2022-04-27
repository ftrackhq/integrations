# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import logging
import ftrack_api
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo
from ftrack_connect_pipeline.constants import asset as asset_const
from ftrack_connect_pipeline import constants


class FtrackAssetBase(object):
    '''Base FtrackAssetBase class.'''

    ftrack_plugin_id = None
    '''Plugin id used on some DCC applications '''

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
    def ftrack_object(self):
        '''
        Returns the current ftrack_object
        '''
        return self._ftrack_object

    @ftrack_object.setter
    def ftrack_object(self, value):
        '''Sets the current ftrack_object'''
        self._ftrack_object = value

    @property
    def loaded(self):
        '''
        Returns If the asset is loaded
        '''
        return self.asset_info[asset_const.IS_LOADED]

    @loaded.setter
    def loaded(self, value):
        '''
        Set the self :obj:`asset_info` as loaded.

        *loaded* True if the objects are loaded in the scene.
        '''
        self.asset_info[asset_const.IS_LOADED] = value

    def __init__(self, event_manager):
        '''
        Initialize FtrackAssetBase with instance of
        :class:`~ftrack_connect_pipeline.event.EventManager`
        '''
        super(FtrackAssetBase, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self._asset_info = None
        self._ftrack_object = None
        self._event_manager = event_manager

    def init_ftrack_object(self, create_object=True):
        '''
        Sets and Returns the current self :py:obj:`ftrack_object`.
        '''
        self.ftrack_object = None
        return self.ftrack_object

    def connect_objects(self, objects):
        '''
        Link the given *objects* under current self :obj:`ftrack_object`
        asset_link attribute.
        '''
        raise NotImplementedError

    def _generate_ftrack_object_name(self):
        '''
        Returns a name for the current self :obj:`ftrack_object` based on
        the first 2 and last 2 characters of the
        :constant:`asset_const.ASSET_INFO_ID`
        '''
        short_id = "{}{}".format(
            self.asset_info[asset_const.ASSET_INFO_ID][:2],
            self.asset_info[asset_const.ASSET_INFO_ID][-2:],
        )
        ftrack_object_name = asset_const.FTRACK_OBJECT_NAME.format(
            self.asset_info[asset_const.CONTEXT_PATH].replace(":", "_"),
            short_id,
        )
        return ftrack_object_name
