# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import random

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants
from ftrack_constants.framework import asset as asset_const

from ftrack_framework_core.asset.asset_info import FtrackAssetInfo


class CommonTestAssetManagerDiscoverPlugin(BasePlugin):
    name = 'common_test_am_discover'
    host_type = constants.host.PYTHON_HOST_TYPE
    plugin_type = constants.plugin.PLUGIN_DISCOVER_TYPE

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=list,
            required_output_value=None
            # required_output_value={
            #    'asset_name': None,
            #    'asset_type_name': None,
            # }
        )

    def run(self, context_data=None, data=None, options=None):
        '''This just a test example of an asset manager discovery plugin providing
        mock data'''
        # filter = {'asset_name': 'torso', 'asset_type_name': 'geo'}
        # return filter

        # Select random asset from anim and geo
        component_names = ['game', 'cache']
        count = 3
        chunk_size = 3

        ftrack_asset_info_list = []
        status = constants.status.SUCCESS_STATUS

        tail = 0
        while len(ftrack_asset_info_list) < count:
            for asset_version_entity in self.session.query(
                'select id, components, components.name, components.id, version, '
                'asset , asset.name, asset.type.name from AssetVersion where '
                'asset_id != None and (asset.type.name=animation or asset.type.name=geometry) '
                'limit {} offset {}'.format(chunk_size, tail)
            ):
                for component in asset_version_entity['components']:
                    if component['name'] in component_names:
                        asset_info = FtrackAssetInfo.create(
                            asset_version_entity, component_id=component['id']
                        )
                        if random.randint(0, 1) == 0:
                            asset_info[asset_const.OBJECTS_LOADED] = True
                        ftrack_asset_info_list.append(asset_info)
                        if len(ftrack_asset_info_list) >= count:
                            break
                if len(ftrack_asset_info_list) >= count:
                    break
            tail += chunk_size

        if not ftrack_asset_info_list:
            status = constants.status.ERROR_STATUS
            self.logger.debug("No discoverable assets in ftrack!")

        print(
            'Discover returning {} discovered asset(s)'.format(
                len(ftrack_asset_info_list)
            )
        )

        if status == constants.status.SUCCESS_STATUS:
            return ftrack_asset_info_list
        else:
            return False, {
                'message': 'Could not gather mock assets from ftrack!'
            }
