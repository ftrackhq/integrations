# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import logging
import ftrack_api
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo
from ftrack_connect_pipeline.constants import asset as asset_const
from ftrack_connect_pipeline import constants


class FtrackAssetBase(object):
    '''Base FtrackAssetBase class.'''

    identity = None
    '''Identifier of the base Node or object in the DCC applications '''

    default_component_name = 'main'
    '''Name of the default component common in most of the published assets'''

    @property
    def component_name(self):
        '''Return component name from the current asset info'''
        return self.asset_info.get(
            asset_const.COMPONENT_NAME, self.default_component_name
        )

    @property
    def asset_version_entity(self):  # ftrack_version(self):
        '''Returns the :class:`ftrack_api.entity.asset_version.AssetVersion`
        object of the current version_id'''
        asset_version_entity = self.session.query(
            'select version from AssetVersion where id is "{}"'.format(
                self.asset_info[asset_const.VERSION_ID]
            )
        ).one()

        return asset_version_entity

    @property
    def is_latest(self):
        '''Returns True if the current version is the latest version'''
        return self.asset_version_entity[asset_const.IS_LATEST_VERSION]

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
        self._event_manager = event_manager

        self._ftrack_object = None

    def set_asset_info(self, asset_info):
        self.asset_info = asset_info

    def init_ftrack_object(self, create_object=True, is_loaded=True):
        '''
        Sets and Returns the current :py:obj:`ftrack_object` for this class.
        '''
        self.ftrack_object = None
        return self.ftrack_object

    def get_ftrack_object(self):
        '''
        Sets and Returns the current :py:obj:`ftrack_object` for this class.
        '''
        self.ftrack_object = None
        return self.ftrack_object

    def connect_objects(self, objects):
        '''
        Parent the given *objects* under current ftrack_object asset link
        attribute
        '''
        raise NotImplementedError

    def _get_unique_ftrack_object_name(self):
        '''Returns a unique scene name for the current asset_name'''
        short_id = "{}{}".format(
            self.asset_info[asset_const.ASSET_INFO_ID][:2],
            self.asset_info[asset_const.ASSET_INFO_ID][-2:],
        )
        ftrack_object_name = asset_const.FTRACK_OBJECT_NAME.format(
            self.asset_info[asset_const.CONTEXT_PATH].replace(":", "_"),
            short_id,
        )
        return ftrack_object_name

    def change_version(self, new_version_id):
        '''
        Updates the current asset_info with the asset_info returned from the
        given *new_version_id*.

        *new_version_id* : Should be an AssetVersion id.
        '''

        asset_version_entity = self.session.query(
            'select version from AssetVersion where id is "{}"'.format(
                new_version_id
            )
        ).one()

        new_asset_info = FtrackAssetInfo.from_version_entity(
            asset_version_entity, self.component_name
        )
        if self.asset_info.session:
            new_asset_info['session'] = self.asset_info.session

        asset_info_options = self.asset_info[asset_const.ASSET_INFO_OPTIONS]

        if asset_info_options:

            asset_context_data = asset_info_options['settings']['context_data']
            asset_data = new_asset_info[asset_const.COMPONENT_PATH]
            asset_context_data[asset_const.ASSET_ID] = new_asset_info[
                asset_const.ASSET_ID
            ]
            asset_context_data[asset_const.VERSION_NUMBER] = new_asset_info[
                asset_const.VERSION_NUMBER
            ]
            asset_context_data[asset_const.ASSET_NAME] = new_asset_info[
                asset_const.ASSET_NAME
            ]
            asset_context_data[asset_const.ASSET_TYPE_NAME] = new_asset_info[
                asset_const.ASSET_TYPE_NAME
            ]
            asset_context_data[asset_const.VERSION_ID] = new_asset_info[
                asset_const.VERSION_ID
            ]

            asset_info_options['settings']['data'][0]['result'] = [asset_data]
            asset_info_options['settings']['context_data'].update(
                asset_context_data
            )

            run_event = ftrack_api.event.base.Event(
                topic=constants.PIPELINE_RUN_PLUGIN_TOPIC,
                data=asset_info_options,
            )

            plugin_result_data = self.session.event_hub.publish(
                run_event, synchronous=True
            )

            result_data = plugin_result_data[0]
            if not result_data:
                self.logger.error("Error re-loading asset")

            new_asset_info[asset_const.ASSET_INFO_OPTIONS] = asset_info_options

            new_asset_info[asset_const.LOAD_MODE] = self.asset_info[
                asset_const.LOAD_MODE
            ]
            new_asset_info[asset_const.REFERENCE_OBJECT] = self.asset_info[
                asset_const.REFERENCE_OBJECT
            ]

            if not new_asset_info:
                self.logger.warning("Asset version couldn't change")
                return
            if not isinstance(new_asset_info, FtrackAssetInfo):
                raise TypeError(
                    "return type of change version has to be type of FtrackAssetInfo"
                )

        self.asset_info.update(new_asset_info)

        return new_asset_info
