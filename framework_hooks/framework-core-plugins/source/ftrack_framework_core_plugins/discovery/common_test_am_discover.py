# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants

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

        # Select first 5 components of type fbx, abc,
        component_name = 'fbx'

        asset_versions_entities = []
        for v in self.session.query(
            'select id, components, components.name, components.id, version, '
            'asset , asset.name, asset.type.name from AssetVersion where '
            'asset_id != None and (asset.type.name=animation or asset.type.name=geometry) limit 3'.format()
        ):
            # if not v['asset']['type']['name'].lower() in ['animation','geometry']:
            #    continue
            do_add = True
            for ev in asset_versions_entities:
                if ev['asset']['id'] == v['asset']['id']:
                    do_add = False
                    break
            if do_add:
                asset_versions_entities.append(v)
                if 10 == len(asset_versions_entities):
                    break

        ftrack_asset_info_list = []
        status = constants.status.SUCCESS_STATUS

        if asset_versions_entities:
            for version in asset_versions_entities:
                asset_info = FtrackAssetInfo.create(version, component_name)
                ftrack_asset_info_list.append(asset_info)

            if not ftrack_asset_info_list:
                status = constants.status.ERROR_STATUS

        else:
            self.logger.debug("No assets in the scene")

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
