# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import json
from functools import partial

from ftrack_framework_core import client
import ftrack_constants as constants


class ResolverClient(client.Client):
    '''
    Asset Resolver Client Base Class
    '''

    definition_filters = [constants.RESOLVER]

    def __init__(self, event_manager):
        '''
        Initialise OpenerClient with instance of
        :class:`~ftrack_framework_core.event.EventManager`
        '''
        super(ResolverClient, self).__init__(event_manager)

    def on_host_changed(self, host_connection):
        '''Asset manager host has been selected, fetch definition. Return False if no definitions.'''

        self.schemas = [
            schema
            for schema in self.host_connection.definitions['schema']
            if schema.get('title').lower() in self.definition_filters
        ]

        # Only one schema available for now
        schema = self.schemas[0]
        schema_title = schema.get('title').lower()
        definitions = self.host_connection.definitions.get(schema_title)
        if len(definitions) > 0:
            # Only one definition for now, we don't have a definition schema on the AM
            self.change_definition(definitions[0], schema)

            self.resolver_plugins = self.definition['resolvers'].get(
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
