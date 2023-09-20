# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import json
from functools import partial

from ftrack_framework_core import client
import ftrack_constants as constants


# TODO: remove Resolver client
class ResolverClient(client.Client):
    '''
    Asset Resolver Client Base Class
    '''

    tool_config_filters = [constants.RESOLVER]

    def __init__(self, event_manager):
        '''
        Initialise OpenerClient with instance of
        :class:`~ftrack_framework_core.event.EventManager`
        '''
        super(ResolverClient, self).__init__(event_manager)

    def on_host_changed(self, host_connection):
        '''Asset manager host has been selected, fetch tool_config. Return False if no tool_configs.'''

        self.schemas = [
            schema
            for schema in self.host_connection.tool_configs['schema']
            if schema.get('title').lower() in self.tool_config_filters
        ]

        # Only one schema available for now
        schema = self.schemas[0]
        schema_title = schema.get('title').lower()
        tool_configs = self.host_connection.tool_configs.get(schema_title)
        if len(tool_configs) > 0:
            # Only one tool_config for now, we don't have a tool_config schema on the AM
            self.change_tool_config(tool_configs[0], schema)

            self.resolver_plugins = self.tool_config['resolvers'].get(
                'resolve_dependencies'
            )
            return True
        else:
            return False

    def resolve_dependencies(
        self, context_id, resolve_dependencies_callback, options=None
    ):
        '''
        Calls the :meth:`~ftrack_framework_core.client.HostConnection.run`
        to run the method
        :meth:`~ftrack_framework_core.host.engine.AssetManagerEngine.resolve_dependencies`
        To fetch list of version dependencies on the given *context_id*.

        Callback received *resolve_dependencies_callback*

        *context_id* : Should be the ID of an existing task.

        *resolve_dependencies_callback* : Callback function that should take the result
        as argument.

        *options* : The options to supply to the plugin.
        '''

        resolver_plugin = self.resolver_plugins[0]

        plugin_type = '{}.{}'.format(
            constants.RESOLVER, resolver_plugin['type']
        )
        data = {
            'method': 'resolve_dependencies',
            'plugin': resolver_plugin,
            'context_id': context_id,
            'plugin_type': plugin_type,
            'options': options,
        }

        self.host_connection.run(
            data,
            self.engine_type,
            callback=partial(
                self._resolve_dependencies_callback,
                resolve_dependencies_callback,
            ),
        )

    def _resolve_dependencies_callback(
        self, resolve_dependencies_callback, event
    ):
        if not event['data']:
            return
        resolve_dependencies_callback(event['data'])
