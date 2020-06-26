# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import ftrack_api
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline import client
from ftrack_connect_pipeline.asset import FtrackAssetBase


class AssetManagerClient(client.Client):
    '''
    Base client class.
    '''

    @property
    def ftrack_asset_list(self):
        '''Return the current list of hosts'''
        return self._ftrack_asset_list

    def __init__(self, event_manager):
        '''Initialise with *event_manager*

        *event_manager* should be the
        :class:`ftrack_connect_pipeline.event.EventManager`instance to
        communicate to the event server.
        '''
        super(AssetManagerClient, self).__init__(event_manager)
        self._ftrack_asset_list = []

    def discover_assets(self, host_id):
        ''' Discovers the available ftrack assets on the given *host_id*'''
        self._discover_assets(host_id)

    def _asset_discovered(self, event):
        '''callback, Assets discovered'''
        if not event['data']:
            return
        for ftrack_asset in event['data']:
            if ftrack_asset not in self.ftrack_asset_list:
                self._ftrack_asset_list.append(ftrack_asset)

        self._connected = True

    def _discover_assets(self, host_id):
        '''Event to discover new available assets in the given *host_id*.'''
        self._ftrack_asset_list = []
        asset_type_filter = []

        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_DISCOVER_ASSETS,
            data={
                'pipeline': {
                    'host_id': host_id,
                    'data': asset_type_filter,
                }
            }
        )
        self._event_manager.publish(event, self._asset_discovered)

    def change_version(self, ftrack_asset_object, asset_version_id):
        '''
        Change the current version of the given *ftrack_asset_object* to the
        given *asset_version_id*

        Note:: this change_version is to be called using the api
        '''
        if not isinstance(ftrack_asset_object, FtrackAssetBase):
            raise TypeError(
                "ftrack_asset_info argument has to be type of FtrackAssetInfo"
            )
        ftrack_asset_object.change_version(asset_version_id)
