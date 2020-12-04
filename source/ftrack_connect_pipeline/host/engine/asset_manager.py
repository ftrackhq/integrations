# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import time

import ftrack_api

from ftrack_connect_pipeline.host.engine import BaseEngine
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.constants import asset as asset_const
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo
from ftrack_connect_pipeline.asset import FtrackAssetBase


class AssetManagerEngine(BaseEngine):
    '''
    Base Asset Manager Engine class.
    '''
    ftrack_asset_class = FtrackAssetBase
    '''Define the class to use for the ftrack node to track the loaded assets'''
    engine_type = 'asset_manager'
    '''Engine type for this engine class'''

    def __init__(self, event_manager, host, hostid, asset_type=None):
        '''
        Initialise HostConnection with instance of
        :class:`~ftrack_connect_pipeline.event.EventManager` , and *host*,
        *hostid* and *asset_type*

        *host* : Host type.. (ex: python, maya, nuke....)

        *hostid* : Host id.

        *asset_type* : Default None. If engine is initialized to publish or load, the asset
        type should be specified.
        '''

        super(AssetManagerEngine, self).__init__(
            event_manager, host, hostid, asset_type=asset_type
        )

    def get_ftrack_asset_object(self, asset_info):
        '''
        Initializes the :data:`ftrack_asset_class` with the given
        *asset_info*

        Returns the initialized :data:`ftrack_asset_class` Class.

        *asset_info* : Should be instance of
        :class:`~ftrack_connect_pipeline.asset.FtrackAssetInfo`
        '''
        ftrack_asset_class = self.ftrack_asset_class(self.event_manager)
        ftrack_asset_class.asset_info = asset_info
        ftrack_asset_class.init_ftrack_object()
        return ftrack_asset_class

    def discover_assets(self, assets=None, options=None, plugin=None):
        '''
        Discover 10 assets from Ftrack with component name main.
        Returns :const:`~ftrack_connnect_pipeline.constants.status` and
        :attr:`ftrack_asset_info_list` which is a list of
        :class:`~ftrack_connect_pipeline.asset.FtrackAssetInfo`
        '''

        start_time = time.time()

        component_name = 'main'
        versions = self.session.query(
            'select id, components, components.name, components.id, version, '
            'asset , asset.name, asset.type.name from AssetVersion where '
            'asset_id != None and components.name is "{0}" limit 10'.format(
                component_name
            )
        ).all()

        ftrack_asset_info_list = []
        status = constants.SUCCESS_STATUS

        if versions:
            for version in versions:
                asset_info = FtrackAssetInfo.from_ftrack_version(
                    version, component_name
                )
                ftrack_asset_info_list.append(asset_info)

            if not ftrack_asset_info_list:
                status = constants.ERROR_STATUS

        else:
            self.logger.debug("No assets in the scene")

        result = ftrack_asset_info_list

        end_time = time.time()
        total_time = end_time - start_time

        result_data = {
            'plugin_name': 'discover_assets',
            'plugin_type': 'action',
            'method': 'discover_assets',
            'status': status,
            'result': result,
            'execution_time': total_time,
            'message': None
        }

        self._notify_client(plugin, result_data)

        return status, result

    def remove_assets(self, assets, options=None, plugin=None):
        '''
        Returns status dictionary and results dictionary keyed by the id for
        executing the :meth:`remove_asset` for all the
        :class:`~ftrack_connect_pipeline.asset.FtrackAssetInfo` in the given
        *assets* list.
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
        (Not implemented for python standalone mode)
        Returns the :const:`~ftrack_connnect_pipeline.constants.status` and the
        result of removing the given *asset_info*

        *asset_info* : :class:`~ftrack_connect_pipeline.asset.FtrackAssetInfo`
        '''

        result = True
        status = constants.SUCCESS_STATUS

        result_data = {
            'plugin_name': 'remove_asset',
            'plugin_type': 'action',
            'method': 'remove_asset',
            'status': status,
            'result': result,
            'execution_time': 0,
            'message': None
        }

        self._notify_client(plugin, result_data)

        return status, result

    def select_assets(self, assets, options=None, plugin=None):
        '''
        Returns status dictionary and results dictionary keyed by the id for
        executing the :meth:`select_asset` for all the
        :class:`~ftrack_connect_pipeline.asset.FtrackAssetInfo` in the given
        *assets* list.
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
        (Not implemented for python standalone mode)
        Returns the :const:`~ftrack_connnect_pipeline.constants.status` and the
        result of selecting the given *asset_info*

        *asset_info* : :class:`~ftrack_connect_pipeline.asset.FtrackAssetInfo`
        '''
        result = False
        message = "Can't select on standalone mode"
        status = constants.ERROR_STATUS

        result_data = {
            'plugin_name': 'select',
            'plugin_type': 'action',
            'method': 'select_asset',
            'status': status,
            'result': result,
            'execution_time': 0,
            'message': message
        }

        self._notify_client(plugin, result_data)

        raise NotImplementedError(message)

    def update_assets(self, assets, options=None, plugin=None):
        '''
        Returns status dictionary and results dictionary keyed by the id for
        executing the :meth:`update_asset` using the criteria of the given
        *plugin* for all the
        :class:`~ftrack_connect_pipeline.asset.FtrackAssetInfo` in the given
        *assets* list.
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
        Returns the :const:`~ftrack_connnect_pipeline.constants.status` and the
        result of updating the given *asset_info* using the criteria of the
        given *plugin*

        *asset_info* : :class:`~ftrack_connect_pipeline.asset.FtrackAssetInfo`

        *options* : Options to update the asset.

        *plugin* : Plugin definition, a dictionary with the plugin information.
        '''
        start_time = time.time()
        status = constants.UNKNOWN_STATUS
        result = []
        message = None

        result_data = {
            'plugin_name': 'update_asset',
            'plugin_type': 'action',
            'method': 'update_asset',
            'status': status,
            'result': result,
            'execution_time': 0,
            'message': message
        }

        if not options:
            options={}
        if plugin:
            plugin_type = '{}.{}'.format('asset_manager', plugin['plugin_type'])

            plugin['plugin_data'] = asset_info

            status, method_result = self._run_plugin(
                plugin, plugin_type,
                data=plugin.get('plugin_data'),
                options=plugin['options'],
                context=None,
                method='run'
            )
            if method_result:
                result = method_result.get(method_result.keys()[0])
            bool_status = constants.status_bool_mapping[status]
            if not bool_status:
                message = "Error executing the plugin: {}".format(plugin)
                self.logger.error(message)

                end_time = time.time()
                total_time = end_time - start_time

                result_data['status'] = status
                result_data['result'] = result
                result_data['execution_time'] = total_time
                result_data['message'] = message

                self._notify_client(plugin, result_data)

                return status, result

            if result:
                options['new_version_id'] = result[0]

                status, result = self.change_version(asset_info, options)

        end_time = time.time()
        total_time = end_time - start_time

        result_data['status'] = status
        result_data['result'] = result
        result_data['execution_time'] = total_time

        self._notify_client(plugin, result_data)

        return status, result

    def change_version(self, asset_info, options, plugin=None):
        '''
        Returns the :const:`~ftrack_connnect_pipeline.constants.status` and the
        result of changing the version of the given *asset_info* to the new
        version id passed in the given *options*

        *asset_info* : :class:`~ftrack_connect_pipeline.asset.FtrackAssetInfo`

        *options* : Options should contain the new_version_id key with the id
        value

        *plugin* : Default None. Plugin definition, a dictionary with the
        plugin information.
        '''
        start_time = time.time()
        status = constants.UNKNOWN_STATUS
        result = {}
        message = None

        result_data = {
            'plugin_name': 'change_version',
            'plugin_type': 'action',
            'method': 'change_version',
            'status': status,
            'result': result,
            'execution_time': 0,
            'message': message
        }

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
            message = str(
                "Error removing asset with version id {} \n error: {} "
                "\n asset_info: {}".format(
                    asset_info[asset_const.VERSION_ID],
                    e,
                    asset_info
                )
            )
            self.logger.error(message)

        bool_status = constants.status_bool_mapping[remove_status]
        if not bool_status:
            end_time = time.time()
            total_time = end_time - start_time

            result_data['status'] = status
            result_data['result'] = result
            result_data['execution_time'] = total_time
            result_data['message'] = message

            self._notify_client(plugin, result_data)

            return remove_status, remove_result

        try:
            new_asset_info = ftrack_asset_object.change_version(new_version_id)
        except Exception, e:
            status = constants.ERROR_STATUS
            message = str(
                "Error changing version of asset with version id {} \n "
                "error: {} \n asset_info: {}".format(
                    asset_info[asset_const.VERSION_ID],
                    e,
                    asset_info
                )
            )
            self.logger.error(message)

            end_time = time.time()
            total_time = end_time - start_time

            result_data['status'] = status
            result_data['result'] = result
            result_data['execution_time'] = total_time
            result_data['message'] = message

            self._notify_client(plugin, result_data)
            return status, result

        if not new_asset_info:
            status = constants.ERROR_STATUS
        else:
            status = constants.SUCCESS_STATUS

        result[asset_info[asset_const.ASSET_INFO_ID]] = new_asset_info

        end_time = time.time()
        total_time = end_time - start_time

        result_data['status'] = status
        result_data['result'] = result
        result_data['execution_time'] = total_time

        self._notify_client(plugin, result_data)

        return status, result

    def run(self, data):
        '''
        Override method of :meth:`~ftrack_connect_pipeline.host.engine
        Executes the method defined in the given *data* method key or in case is
        not given will execute the :meth:`_run_plugin` with the provided *data*
        plugin key.
        Returns the result of the executed method or plugin.

        *data* : pipeline['data'] provided from the client host connection at
        :meth:`~ftrack_connect_pipeline.client.HostConnection.run`
        '''

        method = data.get('method', '')
        plugin = data.get('plugin', None)
        assets = data.get('assets', None)
        options = data.get('options', {})
        plugin_type = data.get('plugin_type', None)

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
            status, method_result = self._run_plugin(
                plugin, plugin_type,
                data=plugin.get('plugin_data'),
                options=plugin['options'],
                context=None,
                method='run'
            )
            if method_result:
                result = method_result.get(method_result.keys()[0])
            bool_status = constants.status_bool_mapping[status]
            if not bool_status:
                raise Exception(
                    'An error occurred during the execution of the plugin {}'
                    '\n status: {} \n result: {}'.format(
                        plugin['plugin'], status, result)
                )

        return result