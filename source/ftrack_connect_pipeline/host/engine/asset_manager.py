# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline.host.engine import BaseEngine
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.constants import asset as asset_const
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo
from ftrack_connect_pipeline.asset import FtrackAssetBase


class AssetManagerEngine(BaseEngine):
    '''
    Base AssetManagerEngine class.
    '''
    ftrack_asset_class = FtrackAssetBase
    engine_type = 'asset_manager'

    def __init__(self, event_manager, host, hostid, asset_type=None):
        '''Initialise AssetManagerEngine with *event_manager*, *host*, *hostid*
        and *asset_type*'''
        super(AssetManagerEngine, self).__init__(
            event_manager, host, hostid, asset_type=asset_type
        )

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

    def get_ftrack_asset_object(self, asset_info):
        '''
        Returns the initialized ftrack_asset_class for the given *asset_info*
        '''
        ftrack_asset_class = self.ftrack_asset_class(self.event_manager)
        ftrack_asset_class.asset_info = asset_info
        ftrack_asset_class.init_ftrack_object()
        return ftrack_asset_class

    def discover_assets(self, assets=None, options=None, plugin=None):
        '''
        Discover 10 assets from Ftrack with component name main.
        Returns status and result
        '''
        status = constants.UNKNOWN_STATUS
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

        if not ftrack_asset_info_list:
            status = constants.ERROR_STATUS
        else:
            status = constants.SUCCESS_STATUS
        result = ftrack_asset_info_list

        return status, result

    def remove_assets(self, assets, options=None, plugin=None):
        '''
        Removes the given *assets*.
        Returns status and result
        '''
        status = None
        result = None
        statuses = {}
        results = {}

        for asset_info in assets:
            try:
                status, result = self.remove_asset(asset_info, options, plugin)
            except Exception, e:
                status = constants.ERROR_STATUS
                self.logger.error(
                    "Error removing asset with version id {} \n error: {} "
                    "\n asset_info: {}".format(
                        asset_info[asset_const.VERSION_ID],
                        e,
                        asset_info
                    )
                )

            bool_status = constants.status_bool_mapping[status]
            statuses[asset_info[asset_const.ASSET_INFO_ID]] = bool_status
            results[asset_info[asset_const.ASSET_INFO_ID]] = result

        return statuses, results

    def remove_asset(self, asset_info, options=None, plugin=None):
        '''
        Removes the given *asset_info*.
        Returns status and result
        '''
        result = True
        status = constants.SUCCESS_STATUS
        return status, result
        #raise NotImplementedError()

    def select_assets(self, assets, options=None, plugin=None):
        '''
        Selects the given *assets*.
        Returns status and result
        '''
        status = None
        result = None
        statuses = {}
        results = {}

        i=0
        for asset_info in assets:
            if i==0:
                options['clear_selection'] = True
            else:
                options['clear_selection'] = False
            try:
                status, result = self.select_asset(asset_info, options, plugin)
            except Exception, e:
                status = constants.ERROR_STATUS
                self.logger.error(
                    "Error selecting asset with version id {} \n error: {} "
                    "\n asset_info: {}".format(
                        asset_info[asset_const.VERSION_ID],
                        e,
                        asset_info
                    )
                )

            bool_status = constants.status_bool_mapping[status]
            statuses[asset_info[asset_const.ASSET_INFO_ID]] = bool_status
            results[asset_info[asset_const.ASSET_INFO_ID]] = result

            i+=1

        return statuses, results

    def select_asset(self, asset_info, options=None, plugin=None):
        '''
        Not Implemented.
        '''
        # result = True
        # status = constants.SUCCESS_STATUS
        # return status, result
        raise NotImplementedError("Can't select on standalone mode")

    def update_assets(self, assets, options=None, plugin=None):
        '''
        Updates the given *assets* using the criteria of the given *plugin*
        Returns status and result
        '''
        status = None
        result = None
        statuses = {}
        results = {}

        for asset_info in assets:
            try:
                status, result = self.update_asset(asset_info, options, plugin)
            except Exception, e:
                status = constants.ERROR_STATUS
                self.logger.error(
                    "Error updating asset with version id {} \n error: {} "
                    "\n asset_info: {}".format(
                        asset_info[asset_const.VERSION_ID],
                        e,
                        asset_info
                    )
                )
            bool_status = constants.status_bool_mapping[status]
            statuses[asset_info[asset_const.ASSET_INFO_ID]] = bool_status
            results[asset_info[asset_const.ASSET_INFO_ID]] = result

        return statuses, results

    def update_asset(self, asset_info, options=None, plugin=None):
        '''
        Updates the given *asset_info* using the criteria of the given *plugin*
        Returns status and result
        '''
        status = constants.UNKNOWN_STATUS
        result = []

        if not options:
            options={}
        if plugin:
            plugin_type = '{}.{}'.format('asset_manager', plugin['plugin_type'])

            plugin['plugin_data'] = asset_info

            status, result = self.run_asset_manager_plugin(
                plugin, plugin_type
            )
            if not status:
                self.logger.debug(
                    "Error executing the plugin: {}".format(plugin)
                )
                return status, result

            if result:
                options['new_version_id'] = result[0]

                status, result = self.change_version(asset_info, options)

        return status, result

    def change_version(self, asset_info, options, plugin=None):
        '''
        Changes the version of the given *asset_info* to the given
        new_version_id in the *options* dictionary.
        Returns status and result
        '''
        status = None
        result = {}

        new_version_id = options['new_version_id']

        ftrack_asset_object = self.get_ftrack_asset_object(asset_info)

        remove_result = None
        remove_status = None
        # first run remove
        try:
            remove_status, remove_result = self.remove_asset(
                asset_info=asset_info, options=None, plugin=None
            )
        except Exception, e:
            remove_status = constants.ERROR_STATUS
            self.logger.error(
                "Error removing asset with version id {} \n error: {} "
                "\n asset_info: {}".format(
                    asset_info[asset_const.VERSION_ID],
                    e,
                    asset_info
                )
            )
        bool_status = constants.status_bool_mapping[remove_status]
        if not bool_status:
            return remove_status, remove_result

        try:
            new_asset_info = ftrack_asset_object.change_version(new_version_id)
        except Exception, e:
            status = constants.ERROR_STATUS
            self.logger.error(
                "Error changing version of asset with version id {} \n "
                "error: {} \n asset_info: {}".format(
                    asset_info[asset_const.VERSION_ID],
                    e,
                    asset_info
                )
            )
            return status, result

        if not new_asset_info:
            status = constants.ERROR_STATUS
        else:
            status = constants.SUCCESS_STATUS

        result[asset_info[asset_const.ASSET_INFO_ID]] = new_asset_info

        return status, result

    def run(self, data):
        '''
        Override function run methods and plugins from the provided *data*
        Return result
        '''
        method = data.get('method')
        plugin = data.get('plugin', None)
        assets = data.get('assets', None)
        options = data.get('options', {})

        result = None

        if hasattr(self, method):
            callback_fn = getattr(self, method)
            status, result = callback_fn(assets, options, plugin)
            if isinstance(status, dict):
                if not all(status.values()):
                    raise Exception(
                        'An error occurred during the execution of '
                        'the method: {}'.format(method)
                    )
            else:
                bool_status = constants.status_bool_mapping[status]
                if not bool_status:
                    raise Exception(
                        'An error occurred during the execution of '
                        'the method: {}'.format(method)
                    )

        elif plugin:
            plugin_type = '{}.{}'.format('asset_manager', plugin['plugin_type'])

            status, result = self.run_asset_manager_plugin(
                plugin, plugin_type
            )

            if not status:
                raise Exception(
                    'An error occurred during the execution of the plugin: {} '
                    '\n type: {}'.format(plugin['plugin'], plugin_type)
                )
        return result
