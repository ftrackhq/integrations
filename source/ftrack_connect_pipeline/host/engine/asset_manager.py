# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline.host.engine import BaseEngine
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo


class AssetManagerEngine(BaseEngine):
    engine_type = 'asset_manager'

    def __init__(self, event_manager, host, hostid, asset_type=None):
        '''Initialise AssetManagerEngine with *event_manager*, *host*, *hostid*
        and *asset_type*'''
        super(AssetManagerEngine, self).__init__(
            event_manager, host, hostid, asset_type=None
        )

    def change_asset_version(self, data):
        '''
        Returns an asset info created from the asset version and component name
        from the given *data*.
        '''
        asset_version = data['data']['asset_version']
        component_name = data['data']['component_name']
        asset_info = FtrackAssetInfo.from_ftrack_version(
            asset_version, component_name
        )
        return asset_info

    def run_asset_manager_plugin(self, plugin, plugin_type):
        '''
        Runs the given asset manager *plugin* of the given *plugin_type* and
        returns the status and the result
        '''
        status, result = self._run_plugin(
            plugin, plugin_type,
            data=plugin.get('plugin_data'),
            options=plugin['options'],
            context=None
        )
        bool_status = constants.status_bool_mapping[status]
        if not bool_status:
            raise Exception(
                'An error occurred during the execution of the Asset Manager '
                'plugin {}\n status: {} \n result: {}'.format(
                    plugin['plugin'], status, result)
            )
        return bool_status, result

    def run(self, data):
        '''
        Override function run packages from the provided *data*
        '''

        plugin_type = '{}.{}'.format('asset_manager', data['plugin_type'])

        status, result = self.run_asset_manager_plugin(
            data, plugin_type
        )
        if not status:
            raise Exception(
                'An error occurred during the execution of the plugin: {} '
                '\n type: {}'.format(data['plugin'],plugin_type)
            )
        return result
