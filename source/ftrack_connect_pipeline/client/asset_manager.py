# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline import client
from ftrack_connect_pipeline.asset import FtrackAssetBase
from ftrack_connect_pipeline.asset import FtrackAssetInfo
from ftrack_connect_pipeline.constants import asset as asset_const


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

    # TODO: remove this as now the asset_info has the key versions to get the
    #  versions
    # def get_asset_versions(self, asset_info):
    #     data = {'method': 'get_asset_versions',
    #             'plugin': None,
    #             'assets': [asset_info]}
    #     self.host_connection.run(
    #         data, self.engine_type, self._asset_versions_callback
    #     )
    # def _asset_versions_callback(self, event):
    #     if not event['data']:
    #         return
    #     for asset_info in event['data']:
    #         print "asset_info"


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

    def _reset_asset_list(self):
        '''Empty the _ftrack_asset_list'''
        self._ftrack_asset_list = []

    def run_discover_assets(self):
        self._reset_asset_list()
        data = {'method': 'discover_assets'}
        self.host_connection.run(
            data, self.engine_type, self._asset_discovered
        )

    def _asset_discovered(self, event):
        '''callback, Assets discovered'''
        if not event['data']:
            return
        for ftrack_asset in event['data']:
            if ftrack_asset not in self.ftrack_asset_list:
                ftrack_asset['session'] = self.session
                self._ftrack_asset_list.append(ftrack_asset)
        self._connected = True

    def change_version(self, asset_info, new_version_id):
        '''
        Change the current version of the given *ftrack_asset_object* to the
        given *asset_version_id*

        Note:: this change_version is to be called using the api

        '''

        data = {'method': 'change_version',
                'plugin': None,
                'assets': asset_info,
                'options': {'new_version_id': new_version_id}
                }
        self.host_connection.run(
            data, self.engine_type, self._change_version_callback
        )
    def _change_version_callback(self, event):
        '''
        Change the current version of the given *ftrack_asset_object* to the
        given *asset_version_id*

        Note:: this change_version is to be called using the api
        '''
        # TODO: if the model doesn't get updated, we should  call the model.set
        #  data after changing the version, so the client can tell the widget to
        #  set the data after the change_version_callback is called.
        if not event['data']:
            return
        data = event['data']
        for k, v in data.items():
            old_info_id = k
            index = None
            i = 0
            for asset_info in self.ftrack_asset_list:
                if asset_info[asset_const.ASSET_INFO_ID] == old_info_id:
                    index = i
                    break
                i += 1
            if index != None:
                self.ftrack_asset_list[index] = v

    def select_assets(self, asset_info_list):
        data = {'method': 'select_assets',
                'plugin': None,
                'assets': asset_info_list
                }
        self.host_connection.run(data, self.engine_type)

    def remove_assets(self, asset_info_list):
        data = {'method': 'remove_assets',
                'plugin': None,
                'assets': asset_info_list
                }
        self.host_connection.run(
            data, self.engine_type, self._remove_assets_callback
        )

    def _remove_assets_callback(self, event):
        if not event['data']:
            return
        data = event['data']
        for k, v in data.items():
            old_info_id = k
            index = None
            i = 0
            for asset_info in self.ftrack_asset_list:
                if asset_info[asset_const.ASSET_INFO_ID] == old_info_id:
                    index = i
                    break
                i += 1
            if index != None:
                self.ftrack_asset_list.pop(index)

    def update_assets(self, asset_info_list, plugin):
        data = {'method': 'update_assets',
                'plugin': plugin,
                'assets': asset_info_list
                }
        self.host_connection.run(
            data, self.engine_type, self._update_assets_callback
        )

    def _update_assets_callback(self, event):
        self.logger.debug(
            "Update assets callback received, event: {}".format(event)
        )
        if not event['data']:
            return
        data = event['data']
        for k, v in data.items():
            old_info_id = k
            index = None
            i=0
            for asset_info in self.ftrack_asset_list:
                if asset_info[asset_const.ASSET_INFO_ID] == old_info_id:
                    index = i
                    break
                i+=1
            if index != None:
                self.ftrack_asset_list[index] = v.get(v.keys()[0])