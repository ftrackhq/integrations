# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import time
import logging
import copy
import ftrack_api
from ftrack_connect_pipeline import utils
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline import client
from ftrack_connect_pipeline.constants import asset as asset_const


class AssetManagerClient(client.Client):
    '''
    Base client class.
    '''

    @property
    def ftrack_asset_list(self):
        '''Return the current list of hosts'''
        return self._ftrack_asset_list

    def __init__(self, event_manager):
        '''Initialise with *event_manager* , and optional *ui* List

        *event_manager* should be the
        :class:`ftrack_connect_pipeline.event.EventManager`instance to
        communicate to the event server.

        *ui* List of valid ui compatibilities.
        '''
        super(AssetManagerClient, self).__init__(event_manager)
        self._ftrack_asset_list = []

    def discover_assets(self, host_id):
        #TODO: we want to return the list mainwhile is been fill it
        self._discover_assets(host_id)

    def _asset_discovered(self, event):
        '''callback, adds new hosts connection from the given *event*'''
        print "asset discovered event ---> {}".format(event)
        if not event['data']:
            return
        for ftrack_asset in event['data']:
            if ftrack_asset not in self.ftrack_asset_list:
                self._ftrack_asset_list.append(ftrack_asset)

        self._connected = True

    def _discover_assets(self, host_id):
        '''Event to discover new available hosts.'''
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

    def change_version(self, asset_version_id):
        pass
        #TODO: call change version from asset base
        #change_version( asset_version_id, self.host_connection.id)
