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

    def __init__(self, event_manager, host_types, host_id, asset_type_name=None):
        '''
        Initialise HostConnection with instance of
        :class:`~ftrack_connect_pipeline.event.EventManager` , and *host*,
        *host_id* and *asset_type_name*

        *host* : Host type.. (ex: python, maya, nuke....)

        *host_id* : Host id.

        *asset_type_name* : Default None. If engine is initialized to publish or load, the asset
        type should be specified.
        '''
        super(AssetManagerEngine, self).__init__(
            event_manager, host_types, host_id, asset_type_name=asset_type_name
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
        asset_versions_entities = self.session.query(
            'select id, components, components.name, components.id, version, '
            'asset , asset.name, asset.type.name from AssetVersion where '
            'asset_id != None and components.name is "{0}" limit 10'.format(
                component_name
            )
        ).all()

        ftrack_asset_info_list = []
        status = constants.SUCCESS_STATUS

        if asset_versions_entities:
            for version in asset_versions_entities:
                asset_info = FtrackAssetInfo.from_version_entity(
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
            'plugin_name': None,
            'plugin_type': constants.PLUGIN_AM_ACTION_TYPE,
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
            except Exception as e:
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

        plugin_type = constants.PLUGIN_AM_ACTION_TYPE
        plugin_name = None
        if plugin:
            plugin_type = '{}.{}'.format('asset_manager', plugin['type'])
            plugin_name = plugin.get('name')

        result_data = {
            'plugin_name': plugin_name,
            'plugin_type': plugin_type,
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
            except Exception as e:
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

        plugin_type = constants.PLUGIN_AM_ACTION_TYPE
        plugin_name = None
        if plugin:
            plugin_type = '{}.{}'.format('asset_manager', plugin['type'])
            plugin_name = plugin.get('name')

        result_data = {
            'plugin_name': plugin_name,
            'plugin_type': plugin_type,
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
            except Exception as e:
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

        plugin_type = constants.PLUGIN_AM_ACTION_TYPE
        plugin_name = None
        if plugin:
            plugin_type = '{}.{}'.format('asset_manager', plugin['type'])
            plugin_name = plugin.get('name')

        result_data = {
            'plugin_name': plugin_name,
            'plugin_type': plugin_type,
            'method': 'update_asset',
            'status': status,
            'result': result,
            'execution_time': 0,
            'message': message
        }

        if not options:
            options={}
        if plugin:

            plugin['plugin_data'] = asset_info

            plugin_result = self._run_plugin(
                plugin, plugin_type,
                data=plugin.get('plugin_data'),
                options=plugin['options'],
                context_data=None,
                method=plugin['default_method']
            )
            if plugin_result:
                status = plugin_result['status']
                result = plugin_result['result'].get(plugin['default_method'])
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

    def load_assets(self, assets, options=None, plugin=None):
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
                status, result = self.load_asset(asset_info, options, plugin)
            except Exception as e:
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

    def load_asset(self, asset_info, options=None, plugin=None):
        '''
        (Not implemented for python standalone mode)
        Returns the :const:`~ftrack_connnect_pipeline.constants.status` and the
        result of removing the given *asset_info*

        *asset_info* : :class:`~ftrack_connect_pipeline.asset.FtrackAssetInfo`
        '''

        # TODO: this contains the import plugin needed info asset_info[asset_const.ASSET_INFO_OPTIONS]

        load_plugin = asset_info[asset_const.ASSET_INFO_OPTIONS]
        plugin_data = load_plugin['settings']['data']
        plugin_options = load_plugin['settings']['options']
        plugin_context_data = load_plugin['settings']['context_data']

        plugin_name = load_plugin['pipeline']['plugin_name']
        plugin_type = load_plugin['pipeline']['plugin_type']
        plugin_method = 'run'
        plugin_category = load_plugin['pipeline']['category']
        plugin_host_type = load_plugin['pipeline']['host_type']

        plugin={
            'category': plugin_category,
            'type': plugin_type.split(".")[-1],
            #'name': 'context selector', #We dont have this information
            'name':None,
            'plugin': plugin_name,
            'widget': None,
            'options': plugin_options,
            'default_method': plugin_method
        }

        start_time = time.time()
        status = constants.UNKNOWN_STATUS
        result = []
        message = None

        # TODO: Maybe we don't want to execute a asset manager plugin,
        #  we want an importer plugin maybe. So, Think about removing this part...
        # plugin_type = constants.PLUGIN_AM_ACTION_TYPE
        # plugin_name = None
        # if plugin:
        #     plugin_type = '{}.{}'.format('asset_manager', plugin['type'])
        #     plugin_name = plugin.get('name')

        result_data = {
            'plugin_name': plugin_name,
            'plugin_type': plugin_type,
            'method': 'load_asset',
            'status': status,
            'result': result,
            'execution_time': 0,
            'message': message
        }

        if not options:
            options={}
        if plugin:

            # plugin['plugin_data'] = asset_info

            plugin_result = self._run_plugin(
                plugin, plugin_type,
                data=plugin_data,
                options=plugin_options,
                context_data=plugin_context_data,
                method=plugin_method
            )
            if plugin_result:
                status = plugin_result['status']
                result = plugin_result['result'].get(plugin_method)
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

            # if result:
            #     options['new_version_id'] = result[0]
            #
            #     status, result = self.change_version(asset_info, options)

        end_time = time.time()
        total_time = end_time - start_time

        result_data['status'] = status
        result_data['result'] = result
        result_data['execution_time'] = total_time

        self._notify_client(plugin, result_data)

        return status, result


    def unload_assets(self, assets, options=None, plugin=None):
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
                status, result = self.unload_asset(asset_info, options, plugin)
            except Exception as e:
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

    def unload_asset(self, asset_info, options=None, plugin=None):
        '''
        (Not implemented for python standalone mode)
        Returns the :const:`~ftrack_connnect_pipeline.constants.status` and the
        result of removing the given *asset_info*

        *asset_info* : :class:`~ftrack_connect_pipeline.asset.FtrackAssetInfo`
        '''

        result = True
        status = constants.SUCCESS_STATUS

        plugin_type = constants.PLUGIN_AM_ACTION_TYPE
        plugin_name = None
        if plugin:
            plugin_type = '{}.{}'.format('asset_manager', plugin['type'])
            plugin_name = plugin.get('name')

        result_data = {
            'plugin_name': plugin_name,
            'plugin_type': plugin_type,
            'method': 'unload_asset',
            'status': status,
            'result': result,
            'execution_time': 0,
            'message': None
        }

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

        plugin_type = constants.PLUGIN_AM_ACTION_TYPE
        plugin_name = None
        if plugin:
            plugin_type = '{}.{}'.format('asset_manager', plugin['type'])
            plugin_name = plugin.get('name')

        result_data = {
            'plugin_name': plugin_name,
            'plugin_type': plugin_type,
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
        except Exception as e:
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
        except Exception as e:
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
        Override method of :meth:`~ftrack_connect_pipeline.host.engine`
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
            plugin_result = self._run_plugin(
                plugin, plugin_type,
                data=plugin.get('plugin_data'),
                options=plugin['options'],
                context_data=None,
                method=plugin['default_method']
            )
            if plugin_result:
                status = plugin_result['status']
                result = plugin_result['result'].get(plugin['default_method'])
            bool_status = constants.status_bool_mapping[status]
            if not bool_status:
                raise Exception(
                    'An error occurred during the execution of the plugin {}'
                    '\n status: {} \n result: {}'.format(
                        plugin['plugin'], status, result)
                )

        return result