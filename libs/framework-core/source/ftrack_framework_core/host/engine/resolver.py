# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import time

from ftrack_framework_core import constants
from ftrack_framework_core.host.engine import BaseEngine


class ResolverEngine(BaseEngine):
    engine_type = constants.RESOLVER
    '''Engine type for this engine class'''

    def __init__(self, event_manager, host_types, host_id, asset_type_name):
        super(ResolverEngine, self).__init__(
            event_manager, host_types, host_id, asset_type_name
        )

    def resolve_dependencies(self, context_id, options=None, plugin=None):
        '''
        Returns a list of the asset versions that task identified by *context_id*
        is depending upon / linked to, with additional options using the given *plugin*.

        *context_id* : id of the task.

        *options* : Options to resolver.

        *plugin* : Plugin definition, a dictionary with the plugin information.
        '''

        start_time = time.time()
        status = constants.UNKNOWN_STATUS
        result = []
        message = None

        plugin_type = constants.PLUGIN_RESOLVE_TYPE
        plugin_name = None
        if plugin:
            plugin_type = '{}.{}'.format(constants.RESOLVER, plugin['type'])
            plugin_name = plugin.get('name')

        result_data = {
            'plugin_name': plugin_name,
            'plugin_type': plugin_type,
            'method': 'resolve_dependencies',
            'status': status,
            'result': result,
            'execution_time': 0,
            'message': message,
        }

        if not options:
            options = {}
        if plugin:
            plugin['plugin_data'] = {'context_id': context_id}

            # Fill in default options from definition
            for key in plugin['options']:
                if not key in options:
                    options[key] = plugin['options'][key]

            plugin_result = self._run_plugin(
                plugin,
                plugin_type,
                data=plugin.get('plugin_data'),
                options=options,
                context_data=None,
                method=plugin['default_method'],
            )

            if plugin_result:
                status = plugin_result['status']
                result = (plugin_result['result'] or {}).get(
                    plugin['default_method']
                )

                if len(plugin_result.get('user_data') or {}) > 0:
                    # Supply user data (message) with result
                    if not isinstance(result, tuple):
                        result = (result, plugin_result['user_data'])

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

        end_time = time.time()
        total_time = end_time - start_time

        result_data['status'] = status
        result_data['result'] = result
        result_data['execution_time'] = total_time

        self._notify_client(plugin, result_data)

        return status, result

    def run(self, data):
        '''
        Override method of :meth:`~ftrack_framework_core.host.engine`
        Executes the method defined in the given *data* method key or in case is
        not given will execute the :meth:`_run_plugin` with the provided *data*
        plugin key.
        Returns the result of the executed method or plugin.

        *data* : pipeline['data'] provided from the client host connection at
        :meth:`~ftrack_framework_core.client.HostConnection.run`
        '''

        method = data.get('method', '')
        plugin = data.get('plugin', None)
        arg = data.get('assets', data.get('context_id'))
        options = data.get('options', {})
        plugin_type = data.get('plugin_type', None)

        result = None

        if hasattr(self, method):
            callback_fn = getattr(self, method)
            status, result = callback_fn(arg, options, plugin)
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
                        'the method "{}"{}'.format(
                            method,
                            (
                                ': {}'.format(result['message'])
                                if result is not None and 'message' in result
                                else ''
                            ),
                        )
                    )

        elif plugin:
            plugin_result = self._run_plugin(
                plugin,
                plugin_type,
                data=plugin.get('plugin_data'),
                options=plugin['options'],
                context_data=None,
                method=plugin['default_method'],
            )
            bool_status = False
            if plugin_result:
                status = plugin_result['status']
                result = plugin_result['result'].get(plugin['default_method'])
                bool_status = constants.status_bool_mapping[status]
            if not bool_status:
                raise Exception(
                    'An error occurred during the execution of the plugin {}'
                    '\n status: {} \n result: {}'.format(
                        plugin['plugin'], status, result
                    )
                )

        return result
