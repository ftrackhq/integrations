# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
from functools import partial

from ftrack_framework_core.client import Client
import ftrack_constants.framework as constants


# TODO: Remove asset manager client
class AssetManagerClient(Client):
    '''
    Asset Manager Client Base Class
    '''

    definition_filters = [constants.definition.ASSET_MANAGER]
    '''Use only definitions that matches the definition_filters'''

    def __init__(self, event_manager, multithreading_enabled=True):
        '''Initialise AssetManagerClient with instance of
        :class:`~ftrack_framework_core.event.EventManager`
        '''
        super(AssetManagerClient, self).__init__(
            event_manager, multithreading_enabled=multithreading_enabled
        )
        self._reset_asset_list()

    def on_host_changed(self, host_connection):
        '''Asset manager host has been selected, fetch definition. Return False if no definitions.'''

        self.schemas = [
            schema
            for schema in self.host_connection.definitions['schema']
            if schema.get('title').lower() in self.definition_filters
        ]

        # Only one definition available for now, we don't have a definition selector
        # on the AM
        schema = self.schemas[0]
        schema_title = schema.get('title').lower()
        definitions = self.host_connection.definitions.get(schema_title)
        if len(definitions) > 0:
            # Only one definition for now, we don't have a definition schema on the AM
            self.change_definition(definitions[0], schema)

            self.menu_action_plugins = self.definition.get('actions')
            #
            # <<<<<<< HEAD:libs/framework-core/source/ftrack_framework_core/client/asset_manager.py
            # self.resolver_plugins = self.definition['resolvers'].get(
            #    'resolve_dependencies'
            # )
            # =======
            # self.discover_plugins = self.definition.get('discover')
            # >>>>>>> backlog/framework-refactor/story:libs/framework-core/source/ftrack_framework_core/client/asset_manager_to_remove.py
            return True
        else:
            return False

    def _reset_asset_list(self):
        '''Empty the :obj:`asset_entities_list`'''
        raise NotImplementedError()

    # Discover

    def discover_assets(self, plugin=None):
        '''
        Runs the provided *plugin* or the first discover plugin in the list, to
        discover assets.

        Callback received at :meth:`_asset_discovered_callback`

        '''
        self._reset_asset_list()

    # <<<<<<< HEAD:libs/framework-core/source/ftrack_framework_core/client/asset_manager.py
    #         if not plugin:
    #             # Use the first discover plugin in the list
    #             plugin = self.menu_action_plugins['discover'][0]
    #         plugin_type = '{}.{}'.format('asset_manager', plugin['type'])
    # =======
    #         plugin_type = None
    #         if plugin:
    #             plugin_type = '{}.{}'.format(
    #                 constants.definition.ASSET_MANAGER, plugin['type']
    #             )
    # >>>>>>> backlog/framework-refactor/story:libs/framework-core/source/ftrack_framework_core/client/asset_manager_to_remove.py
    #         data = {
    #             'plugin': plugin,
    #             'plugin_type': plugin_type,
    #         }
    # <<<<<<< HEAD:libs/framework-core/source/ftrack_framework_core/client/asset_manager.py
    #
    #         self.host_connection.run(
    # =======
    #         self.host_connection.run_definition(
    # >>>>>>> backlog/framework-refactor/story:libs/framework-core/source/ftrack_framework_core/client/asset_manager_to_remove.py
    #             data, self.engine_type, callback=self._asset_discovered_callback
    #         )

    def _asset_discovered_callback(self, event):
        '''Callback of the :meth:`discover_assets`'''
        raise NotImplementedError()

    # Load

    def load_assets(self, asset_info_list):
        '''
        Calls the :meth:`~ftrack_framework_core.client.HostConnection.run`
        to run the method
        :meth:`~ftrack_framework_core.host.engine.AssetManagerEngine.load_assets`
        To load the assets of the given *asset_info_list*.

        Callback received at :meth:`_load_assets_callback`

        *asset_info_list* : Should a list pf be instances of
        :class:`~ftrack_framework_core.asset.FtrackAssetInfo`
        '''

        data = {
            'method': 'load_assets',
            'plugin': None,
            'assets': asset_info_list,
        }
        self.host_connection.run_definition(
            data, self.engine_type, callback=self._load_assets_callback
        )

    def _load_assets_callback(self, event):
        '''
        Callback of the :meth:`load_assets`
        Updates the current asset_entities_list
        '''
        raise NotImplementedError()

    # Select

    def select_assets(self, asset_info_list, plugin):
        '''
        Select the assets of the given *asset_info_list*, by running the *plugin*.

        *asset_info_list* : Should a list pf be instances of
        :class:`~ftrack_framework_core.asset.FtrackAssetInfo`
        '''
        if not plugin:
            # Use the first discover plugin in the list
            plugin = self.menu_action_plugins['discover'][0]
        plugin_type = '{}.{}'.format('asset_manager', plugin['type'])
        plugin['plugin_data'] = asset_info_list
        data = {
            'plugin': plugin,
            'plugin_type': plugin_type,
        }
        self.host_connection.run_definition(data, self.engine_type)

    def select_asset(self, plugin, asset_info):
        '''
        *asset_info* : Should a list pf be instances of
        :class:`~ftrack_framework_core.asset.FtrackAssetInfo`
        '''
        self.select_assets([asset_info], plugin)

    # Update

    def update_assets(self, asset_info_list, plugin):
        '''
        Calls the :meth:`~ftrack_framework_core.client.HostConnection.run`
        to run the method
        :meth:`~ftrack_framework_core.host.engine.AssetManagerEngine.update_assets`
        To update to the last version the assets of the given *asset_info_list*.

        Callback received at :meth:`_update_assets_callback`

        *asset_info_list* : Should a list pf be instances of
        :class:`~ftrack_framework_core.asset.FtrackAssetInfo`

        *plugin* : The plugin definition of the plugin to run during the update_assets
        method
        '''
        plugin_type = None
        if plugin:
            plugin_type = '{}.{}'.format(
                constants.definition.ASSET_MANAGER, plugin['type']
            )
        data = {
            'method': 'update_assets',
            'plugin': plugin,
            'assets': asset_info_list,
            'plugin_type': plugin_type,
        }
        self.host_connection.run_definition(
            data, self.engine_type, callback=self._update_assets_callback
        )

    def _update_assets_callback(self, event):
        '''
        Callback of the :meth:`update_assets`
        Updates the current asset_entities_list
        '''
        raise NotImplementedError()

    # Change version

    def change_version(self, asset_info, new_version_id):
        '''
        Calls the :meth:`ftrack_framework_core.client.HostConnection.run`
        to run the method
        :meth:`ftrack_framework_core.host.engine.AssetManagerEngine.change_version`
        To change the version of the given *asset_info*.

        Callback received at :meth:`_change_version_callback`

        *asset_info* : Should be instance of
        :class:`ftrack_framework_core.asset.FtrackAssetInfo`

        *new_version_id* : Should be an AssetVersion id.
        '''

        data = {
            'method': 'change_version',
            'plugin': None,
            'assets': asset_info,
            'options': {'new_version_id': new_version_id},
        }
        self.host_connection.run_definition(
            data, self.engine_type, callback=self._change_version_callback
        )

    def _change_version_callback(self, event):
        '''
        Callback of the :meth:`change_version`
        Updates the current asset_entities_list
        '''
        raise NotImplementedError()

    # Unload assets

    def unload_assets(self, asset_info_list):
        '''
        Calls the :meth:`~ftrack_framework_core.client.HostConnection.run`
        to run the method
        :meth:`~ftrack_framework_core.host.engine.AssetManagerEngine.unload_assets`
        To unload the assets of the given *asset_info_list*.

        Callback received at :meth:`_unload_assets_callback`

        *asset_info_list* : Should a list pf be instances of
        :class:`~ftrack_framework_core.asset.FtrackAssetInfo`
        '''

        data = {
            'method': 'unload_assets',
            'plugin': None,
            'assets': asset_info_list,
        }
        self.host_connection.run_definition(
            data, self.engine_type, callback=self._unload_assets_callback
        )

    def _unload_assets_callback(self, event):
        '''
        Callback of the :meth:`unload_assets`
        Updates the current asset_entities_list
        '''
        raise NotImplementedError()

    # Remove assets

    def remove_assets(self, asset_info_list):
        '''
        Calls the :meth:`~ftrack_framework_core.client.HostConnection.run`
        to run the method
        :meth:`~ftrack_framework_core.host.engine.AssetManagerEngine.remove_assets`
        To remove the assets of the given *asset_info_list*.

        Callback received at :meth:`_remove_assets_callback`

        *asset_info_list* : Should a list pf be instances of
        :class:`~ftrack_framework_core.asset.FtrackAssetInfo`
        '''

        data = {
            'method': 'remove_assets',
            'plugin': None,
            'assets': asset_info_list,
        }
        self.host_connection.run_definition(
            data, self.engine_type, callback=self._remove_assets_callback
        )

    def _remove_assets_callback(self, event):
        '''
        Callback of the :meth:`remove_assets`
        Updates the current asset_entities_list
        '''
        raise NotImplementedError()
