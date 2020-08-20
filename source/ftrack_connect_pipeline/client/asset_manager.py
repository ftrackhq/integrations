# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline import client
from ftrack_connect_pipeline.asset import FtrackAssetBase


class AssetManagerClient(client.Client):
    '''
    Base client class.
    '''

    @property
    def event_manager(self):
        return self._event_manager

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
        self._reset_asset_list()

    def change_host(self, host_connection):
        ''' Triggered when definition_changed is called from the host_selector.
        Generates the widgets interface from the given *host_connection*,
        *schema* and *definition*'''
        super(AssetManagerClient, self).change_host(host_connection)

        self.schemas = [
            schema for schema in self.host_connection.definitions['schema']
            if schema.get('title').lower() == 'asset_manager'
        ]
        #Only one schema available for now, we Don't have a schema selector
        # on the AM
        schema = self.schemas[0]
        schema_title = schema.get('title').lower()
        definitions = self.host_connection.definitions.get(schema_title)
        #Only one definition for now, we don't have a definition schema on the
        # AM
        self.definition = definitions[0]
        self.engine_type = self.definition['_config']['engine_type']

        self.menu_action_plugins = self.definition['actions']
        #self.discover_plugins = self.definition['discover']

    def _asset_discovered(self, event):
        '''callback, Assets discovered'''
        if not event['data']:
            return
        for ftrack_asset in event['data']:
            if ftrack_asset not in self.ftrack_asset_list:
                ftrack_asset.definition = self.definition
                self._ftrack_asset_list.append(ftrack_asset)
        self._connected = True

    def _reset_asset_list(self):
        '''Empty the _ftrack_asset_list'''
        self._ftrack_asset_list = []

    def _run_discover_assets(self):
        self._reset_asset_list()
        data = {'method': 'discover_assets',
                'plugin': None,
                'assets': None}
        self.host_connection.run(
            data, self.engine_type, self._asset_discovered
        )

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
        ftrack_asset_object.change_version(
            asset_version_id, self.host_connection
        )
