# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline import client
from ftrack_connect_pipeline.constants import asset as asset_const


class AssetManagerClient(client.Client):
    '''
    Asset Manager Client Base Class
    '''
    definition_filter = 'asset_manager'
    '''Use only definitions that matches the definition_filter'''

    @property
    def ftrack_asset_list(self):
        '''Return the current list of asset_info'''
        return self._ftrack_asset_list

    def __init__(self, event_manager):
        '''Initialise AssetManagerClient with instance of
        :class:`~ftrack_connect_pipeline.event.EventManager`
        '''
        super(AssetManagerClient, self).__init__(event_manager)
        self._reset_asset_list()

    def change_host(self, host_connection):
        super(AssetManagerClient, self).change_host(host_connection)

        self.schemas = [
            schema for schema in self.host_connection.definitions['schema']
            if schema.get('title').lower() == self.definition_filter
        ]

        #Only one schema available for now, we Don't have a schema selector
        # on the AM
        schema = self.schemas[0]
        schema_title = schema.get('title').lower()
        definitions = self.host_connection.definitions.get(schema_title)
        #Only one definition for now, we don't have a definition schema on the
        # AM
        self.change_definition(schema, definitions[0])

        self.menu_action_plugins = self.definition.get('actions')
        self.discover_plugins = self.definition.get('discover')

    def _reset_asset_list(self):
        '''Empty the :obj:`ftrack_asset_list`'''
        self._ftrack_asset_list = []

    def discover_assets(self, plugin=None):
        '''
        Calls the :meth:`ftrack_connect_pipeline.client.HostConnection.run`
        to run the method
        :meth:`ftrack_connect_pipeline.host.engine.AssetManagerEngine.discover_assets`

        Callback received at :meth:`_asset_discovered_callback`

        *plugin* : Optional plugin to be run in the method.
        (Not implremented yet)
        '''
        self._reset_asset_list()
        plugin_type = None
        if plugin:
            plugin_type = '{}.{}'.format('asset_manager', plugin['plugin_type'])
        data = {
            'method': 'discover_assets',
            'plugin': plugin,
            'plugin_type': plugin_type
        }
        self.host_connection.run(
            data, self.engine_type, self._asset_discovered_callback
        )

    def _asset_discovered_callback(self, event):
        '''Callback of the :meth:`discover_assets`'''
        if not event['data']:
            return
        for ftrack_asset in event['data']:
            if ftrack_asset not in self.ftrack_asset_list:
                ftrack_asset['session'] = self.session
                self._ftrack_asset_list.append(ftrack_asset)
        self._connected = True

    def change_version(self, asset_info, new_version_id):
        '''
        Calls the :meth:`ftrack_connect_pipeline.client.HostConnection.run`
        to run the method
        :meth:`ftrack_connect_pipeline.host.engine.AssetManagerEngine.change_version`
        To change the version of the given *asset_info*.

        Callback received at :meth:`_change_version_callback`

        *asset_info* : Should be instance of
        :class:`ftrack_connect_pipeline.asset.FtrackAssetInfo`

        *new_version_id* : Should be an AssetVersion id.
        '''

        data = {
            'method': 'change_version',
            'plugin': None,
            'assets': asset_info,
            'options': {'new_version_id': new_version_id}
        }
        self.host_connection.run(
            data, self.engine_type, self._change_version_callback
        )

    def select_assets(self, asset_info_list):
        '''
        Calls the :meth:`~ftrack_connect_pipeline.client.HostConnection.run`
        to run the method
        :meth:`~ftrack_connect_pipeline.host.engine.AssetManagerEngine.select_assets`
        To select the assets of the given *asset_info_list*

        *asset_info_list* : Should a list pf be instances of
        :class:`~ftrack_connect_pipeline.asset.FtrackAssetInfo`
        '''
        data = {
            'method': 'select_assets',
            'plugin': None,
            'assets': asset_info_list
        }
        self.host_connection.run(data, self.engine_type)

    def remove_assets(self, asset_info_list):
        '''
        Calls the :meth:`~ftrack_connect_pipeline.client.HostConnection.run`
        to run the method
        :meth:`~ftrack_connect_pipeline.host.engine.AssetManagerEngine.remove_assets`
        To remove the assets of the given *asset_info_list*.

        Callback received at :meth:`_remove_assets_callback`

        *asset_info_list* : Should a list pf be instances of
        :class:`~ftrack_connect_pipeline.asset.FtrackAssetInfo`
        '''

        data = {
            'method': 'remove_assets',
            'plugin': None,
            'assets': asset_info_list
        }
        self.host_connection.run(
            data, self.engine_type, self._remove_assets_callback
        )

    def update_assets(self, asset_info_list, plugin):
        '''
        Calls the :meth:`~ftrack_connect_pipeline.client.HostConnection.run`
        to run the method
        :meth:`~ftrack_connect_pipeline.host.engine.AssetManagerEngine.update_assets`
        To update to the last version the assets of the given *asset_info_list*.

        Callback received at :meth:`_update_assets_callback`

        *asset_info_list* : Should a list pf be instances of
        :class:`~ftrack_connect_pipeline.asset.FtrackAssetInfo`

        *plugin* : The plugin definition of the plugin to run during the update_assets
        method
        '''
        plugin_type = None
        if plugin:
            plugin_type = '{}.{}'.format('asset_manager', plugin['plugin_type'])
        data = {
            'method': 'update_assets',
            'plugin': plugin,
            'assets': asset_info_list,
            'plugin_type': plugin_type
        }
        self.host_connection.run(
            data, self.engine_type, self._update_assets_callback
        )

    def _find_asset_info_by_id(self, id):
        '''
        Returns an instance of the
        :class:`~ftrack_connect_pipeline.asset.FtrackAssetInfo` if the given
        *id* matches an
        :const:`~ftrack_connnect_pipeline.constants.asset.ASSET_INFO_ID`
        of an object in :obj:`ftrack_asset_list`
        '''
        asset_info = next((sub for sub in self.ftrack_asset_list if sub[asset_const.ASSET_INFO_ID] == id), None)
        if not asset_info:
            self.logger.warning('No asset info found for id {}'.format(id))
        return asset_info

    def _change_version_callback(self, event):
        '''
        Callback of the :meth:`change_version`
        Updates the current ftrack_asset_list
        '''

        if not event['data']:
            return
        data = event['data']
        for key, value in data.items():
            asset_info = self._find_asset_info_by_id(key)
            index = self.ftrack_asset_list.index(asset_info)
            if index is None:
                continue
            self.logger.info('Removing id {} with index {}'.format(key, index))
            self.ftrack_asset_list[index] = value

    def _remove_assets_callback(self, event):
        '''
        Callback of the :meth:`remove_assets`
        Updates the current ftrack_asset_list
        '''
        if not event['data']:
            return
        data = event['data']

        for key, value in data.items():
            asset_info = self._find_asset_info_by_id(key)
            index = self.ftrack_asset_list.index(asset_info)
            if index is None:
                continue
            self.logger.info('Removing id {} with index {}'.format(key, index))
            self.ftrack_asset_list.pop(index)

    def _update_assets_callback(self, event):
        '''
        Callback of the :meth:`update_assets`
        Updates the current ftrack_asset_list
        '''
        if not event['data']:
            return
        data = event['data']
        for key, value in data.items():
            asset_info = self._find_asset_info_by_id(key)
            index = self.ftrack_asset_list.index(asset_info)
            if index is None:
                continue
            self.logger.info('Updating id {} with index {}'.format(key, index))
            self.ftrack_asset_list[index] = value.get(value.keys()[0])
