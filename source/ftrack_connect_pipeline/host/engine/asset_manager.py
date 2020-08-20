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

    def discover_assets(self, plugin, assets):
        component_name = 'main'
        versions = self.session.query(
            'select id, components, components.name, components.id, version, '
            'asset , asset.name, asset.type.name from AssetVersion where '
            'asset_id != None and components.name is "{0}" limit 10'.format(
                component_name
            )
        ).all()

        component_name = 'main'

        ftrack_asset_info_list = []

        for version in versions:
            asset_info = FtrackAssetInfo.from_ftrack_version(
                version, component_name
            )
            ftrack_asset_info_list.append(asset_info)

        # ftrack_asset_list = []
        #
        # for asset_info in ftrack_asset_info_list:
        #     ftrack_asset_class = FtrackAssetBase(self.event_manager)
        #     ftrack_asset_class.asset_info = asset_info
        #     ftrack_asset_class.init_ftrack_object()
        #     ftrack_asset_list.append(ftrack_asset_class)

        return ftrack_asset_info_list


    def run(self, data):
        '''
        Override function run packages from the provided *data*
        '''
        method = data.get('method')
        plugin = data.get('plugin')
        assets = data.get('assets')

        result = None

        if hasattr(self, method):
            callback_fn = getattr(self, method)
            status, result = callback_fn(plugin, assets)
            if not status:
                raise Exception(
                    'An error occurred during the execution of '
                    'the method: {}'.format(method)
                )

        elif plugin:
            plugin_type = '{}.{}'.format('asset_manager', data['plugin_type'])

            status, result = self.run_asset_manager_plugin(
                data, plugin_type
            )

            if not status:
                raise Exception(
                    'An error occurred during the execution of the plugin: {} '
                    '\n type: {}'.format(plugin, plugin_type)
                )
        return result
