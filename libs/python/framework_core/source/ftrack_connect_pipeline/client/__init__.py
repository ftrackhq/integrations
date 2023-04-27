# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
import os
import time
import logging
import copy
import uuid

from six import string_types
import ftrack_api
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.log import LogDB
from ftrack_connect_pipeline.log.log_item import LogItem
from ftrack_connect_pipeline.definition import definition_object


class HostConnection(object):
    '''
    Host Connection Base class.
    This class is used to communicate between the client and the host.
    '''

    @property
    def context_id(self):
        '''Returns the current context id as fetched from the host'''
        return self._context_id

    @context_id.setter
    def context_id(self, value):
        '''Set the context id for this host connection to *value*. Will notify the host and
        other active host connection through an event, and tell the client through callback.'''
        if value == self.context_id:
            return
        self._context_id = value

    @property
    def event_manager(self):
        '''Returns instance of
        :class:`~ftrack_connect_pipeline.event.EventManager`'''
        return self._event_manager

    @property
    def session(self):
        '''
        Returns instance of :class:`ftrack_api.session.Session`
        '''
        return self.event_manager.session

    @property
    def definitions(self):
        '''Returns the current definitions, filtered on discoverable.'''
        context_identifiers = []
        if self.context_id:

            entity = self.session.query(
                'TypedContext where id is {}'.format(self.context_id)
            ).first()
            if entity:
                # Task, Project,...
                context_identifiers.append(entity.get('context_type').lower())
                if 'type' in entity:
                    # Modeling, animation...
                    context_identifiers.append(
                        entity['type'].get('name').lower()
                    )
                # Name of the task or the project
                context_identifiers.append(entity.get('name').lower())

        if context_identifiers:
            result = {}
            for schema_title in self._raw_host_data['definition'].keys():
                result[schema_title] = self._filter_definitions(
                    context_identifiers,
                    self._raw_host_data['definition'][schema_title],
                )
            # TODO:
            #  This is a dictionary where the keys are the definition types like
            #  publisher, opener, etc... and the values are a list of those.
            #  But it also includes the key Schema, which contains a list of the
            #  schemas for each type. This should be cleaned up in the future in
            #  order to separate schemas from the definitions.
            return copy.deepcopy(result)

        return definition_object.DefinitionObject(
            self._raw_host_data['definition']
        )

    def _filter_definitions(self, context_identifiers, definitions):
        '''Filter *definitions* on *context_identifiers* and discoverable.'''
        result = []
        for definition in definitions:
            match = False
            discoverable = definition.get('discoverable')
            if not discoverable:
                # Append if not discoverable, because that means should be
                # discovered always as the Asset Manager or the logger
                match = True
            else:
                # This is not in a list comprehension because it needs the break
                # once found
                for discover_name in discoverable:
                    if discover_name.lower() in context_identifiers:
                        # Add definition as it matches
                        match = True
                        break

            if not match:
                self.logger.debug(
                    'Excluding definition {} - context identifiers {} '
                    'does not match schema discoverable: {}.'.format(
                        definition.get('name'),
                        context_identifiers,
                        discoverable,
                    )
                )
            if match:
                result.append(definition)

        # Convert the list to our custom DefinitionList so we can have get
        # method and automatically convert all definitions to definitionObject
        return definition_object.DefinitionList(result)

    @property
    def id(self):
        '''Returns the current host id.'''
        return self._raw_host_data['host_id']

    @property
    def name(self):
        '''Returns the current host name.'''
        return self._raw_host_data['host_name']

    @property
    def host_types(self):
        '''Returns the list of compatible host for the current definitions.'''
        return self._raw_host_data['host_id'].split("-")[0].split(".")

    def __del__(self):
        self.logger.debug('Closing {}'.format(self))

    def __repr__(self):
        return '<HostConnection: {}>'.format(self.id)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __init__(self, event_manager, host_data):
        '''Initialise HostConnection with instance of
        :class:`~ftrack_connect_pipeline.event.EventManager` , and *host_data*

        *host_data* : Dictionary containing the host information.
        :py:func:`~ftrack_connect_pipeline.host.provide_host_information`

        '''
        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )

        copy_data = copy.deepcopy(host_data)

        self._event_manager = event_manager
        self._raw_host_data = copy_data
        self._context_id = self._raw_host_data.get('context_id')
        self.subscribe_host_context_change()

    def run(self, data, engine, callback=None):
        '''
        Publish an event with the topic
        :py:const:`~ftrack_connect_pipeline.constants.PIPELINE_HOST_RUN`
        with the given *data* and *engine*.
        '''
        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_HOST_RUN,
            data={
                'pipeline': {
                    'host_id': self.id,
                    'data': data,
                    'engine_type': engine,
                }
            },
        )
        self.event_manager.publish(event, callback)

    def launch_client(self, name, source=None):
        '''Send a widget launch event, to be picked up by DCC.'''
        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_CLIENT_LAUNCH,
            data={
                'pipeline': {
                    'host_id': self.id,
                    'name': name,
                    'source': source,
                }
            },
        )
        self.event_manager.publish(
            event,
        )

    def subscribe_host_context_change(self):
        '''Have host connection subscribe to context change events, to be able
        to notify client'''
        self.session.event_hub.subscribe(
            'topic={} and data.pipeline.host_id={}'.format(
                constants.PIPELINE_HOST_CONTEXT_CHANGE, self.id
            ),
            self._ftrack_host_context_id_changed,
        )

    def _ftrack_host_context_id_changed(self, event):
        '''Set the new context ID based on data provided in *event*'''
        self.context_id = event['data']['pipeline']['context_id']

    def change_host_context_id(self, context_id):
        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_CLIENT_CONTEXT_CHANGE,
            data={'pipeline': {'host_id': self.id, 'context_id': context_id}},
        )
        self.event_manager.publish(
            event,
        )


class Client(object):
    '''
    Base client class.
    '''

    ui_types = [constants.UI_TYPE]
    '''Compatible UI for this client.'''
    definition_filters = None
    '''Use only definitions that matches the definition_filters'''
    definition_extensions_filter = None
    '''(Open) Only show definitions and components capable of accept these filename extensions. '''

    _host_connection = None
    '''The singleton host connection used by all clients within the process space / DCC'''
    _host_connections = []
    '''The list of discovered host connections'''

    def __repr__(self):
        return '<Client:{0}>'.format(self.ui_types)

    @property
    def session(self):
        '''
        Returns instance of :class:`ftrack_api.session.Session`
        '''
        return self._event_manager.session

    @property
    def event_manager(self):
        '''Returns instance of
        :class:`~ftrack_connect_pipeline.event.EventManager`'''
        return self._event_manager

    @property
    def connected(self):
        '''
        Returns True if client is connected to a
        :class:`~ftrack_connect_pipeline.host.HOST`'''
        return self._connected

    @property
    def context_id(self):
        '''Returns the current context id from host'''
        if self.host_connection is None:
            raise Exception('No host connection available')
        return self.host_connection.context_id

    @context_id.setter
    def context_id(self, context_id):
        '''Sets the context id on current host connection, will throw an exception
        if no host connection is active'''
        if not isinstance(context_id, string_types):
            raise ValueError('Context should be in form of a string.')
        if self.host_connection is None:
            raise Exception('No host connection available')
        self.host_connection.change_host_context_id(context_id)

    @property
    def context(self):
        '''Returns the current context'''
        if self.host_connection is None:
            raise Exception('No host connection available')
        if self.host_connection.context_id is None:
            raise Exception('No host context id set')
        return self.session.query(
            'Context where id={}'.format(self.context_id)
        ).first()

    @property
    def host_connections(self):
        '''Return the current list of host_connections'''
        return Client._host_connections

    @host_connections.setter
    def host_connections(self, value):
        '''Return the current list of host_connections'''
        Client._host_connections = value

    @property
    def host_connection(self):
        '''
        Return instance of
        :class:`~ftrack_connect_pipeline.client.HostConnection`
        '''
        return Client._host_connection

    @host_connection.setter
    def host_connection(self, value):
        '''
        Assign the host_connection to the given *value*

        *value* : should be instance of
        :class:`~ftrack_connect_pipeline.client.HostConnection`
        '''
        if value is None or (
            self.host_connection and value.id == self.host_connection.id
        ):
            return

        self.logger.debug('host connection: {}'.format(value))
        Client._host_connection = value
        self.on_client_notification()
        self.subscribe_host_context_change()
        # Feed change of host and context to client
        self.on_host_changed(self.host_connection)
        self.on_context_changed(self.host_connection.context_id)

    @property
    def schema(self):
        '''Return the current schema.'''
        return self._schema

    @property
    def definition(self):
        '''Returns the current definition.'''
        return self._definition

    @property
    def definitions(self):
        '''Returns the definitions list of the current host connection'''
        if self.host_connection is None:
            raise Exception('No host connection available')
        return self.host_connection.definitions

    @property
    def engine_type(self):
        '''Return the current engine type'''
        return self._engine_type

    @property
    def logs(self):
        '''Return the log items'''
        self._init_logs()
        return self._logs.get_log_items(
            self.host_connection.id
            if not self.host_connection is None
            else None
        )

    def _init_logs(self):
        '''Delayed initialization of logs, when we know host ID.'''
        if self._logs is None:
            self._logs = LogDB(
                self.host_connection.id
                if not self.host_connection is None
                else uuid.uuid4().hex
            )

    @property
    def multithreading_enabled(self):
        '''Return True if DCC supports multithreading (write operations)'''
        return self._multithreading_enabled

    def __init__(self, event_manager, multithreading_enabled=True):
        '''
        Initialise Client with instance of
        :class:`~ftrack_connect_pipeline.event.EventManager`
        '''
        self._current = {}
        self.context_change_subscribe_id = None
        self._connected = False
        self._logs = None
        self._schema = None
        self._definition = None

        self.__callback = None
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self._event_manager = event_manager
        self.logger.debug('Initialising {}'.format(self))
        self._multithreading_enabled = multithreading_enabled

    # Host

    def discover_hosts(self, force_rediscover=False, time_out=3):
        '''
        Find for available hosts during the optional *time_out* and Returns
        a list of discovered :class:`~ftrack_connect_pipeline.client.HostConnection`.

        Skip this and use existing singleton host connection if previously detected,
        unless *force_rediscover* is True.
        '''
        if force_rediscover:
            self.host_connections = None
            self.host_connection = None
        if self.host_connection is not None:
            self.on_client_notification()
            self.subscribe_host_context_change()
            self.on_host_changed(self.host_connection)
            self.on_context_changed(self.host_connection.context_id)
            return
        # discovery host loop and timeout.
        start_time = time.time()
        self.logger.debug('time out set to {}:'.format(time_out))
        if not time_out:
            self.logger.warning(
                'Running client with no time out.'
                'Will not stop until discover a host.'
                'Terminate with: Ctrl-C'
            )

        while not self.host_connections:
            delta_time = time.time() - start_time

            if time_out and delta_time >= time_out:
                self.logger.warning('Could not discover any host.')
                break

            self._discover_hosts()

        if self.__callback and self.host_connections:
            self.__callback(self.host_connections)

        # Feed host connections to the client
        self.on_hosts_discovered(self.host_connections)

    def _discover_hosts(self):
        '''
        Publish an event with the topic
        :py:data:`~ftrack_connect_pipeline.constants.PIPELINE_DISCOVER_HOST`
        with the callback
        py:meth:`~ftrack_connect_pipeline.client._host_discovered`
        '''
        self.host_connections = []  # Start over
        discover_event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_DISCOVER_HOST
        )

        self._event_manager.publish(
            discover_event, callback=self._host_discovered
        )

    def _host_discovered(self, event):
        '''
        Callback, add the :class:`~ftrack_connect_pipeline.client.HostConnection`
        of the new discovered :class:`~ftrack_connect_pipeline.host.HOST` from
        the given *event*.

        *event*: :class:`ftrack_api.event.base.Event`
        '''
        if not event['data']:
            return
        host_connection = HostConnection(self.event_manager, event['data'])
        if (
            host_connection
            and host_connection not in self.host_connections
            and self.filter_host(host_connection)
        ):
            Client._host_connections.append(host_connection)

        self._connected = True

    def filter_host(self, host_connection):
        '''Return True if the *host_connection* should be considered

        *host_connection*: :class:`ftrack_connect_pipeline.client.HostConnection`
        '''
        # On the discovery time context id could be None, so we have to consider
        # hosts with non context id. This method could be useful later on to
        # filter hosts that not match a specific criteria. But considering all
        # hosts as valid for now.
        return True

    def change_host(self, host_connection):
        '''Client(user) has chosen the host connection to use, set it to *host_connection*'''
        self.host_connection = host_connection

    def on_hosts_discovered(self, host_connections):
        '''Callback, hosts has been discovered. To be overridden by the qt client'''
        pass

    def on_host_changed(self, host_connection):
        '''Called when the host has been (re-)selected by the user. To be
        overridden by the qt client.'''
        pass

    # Context

    def subscribe_host_context_change(self):
        '''Have host connection subscribe to context change events, to be able
        to notify client'''
        if self.context_change_subscribe_id:
            self.session.unsubscribe(self.context_change_subscribe_id)
        self.context_change_subscribe_id = self.session.event_hub.subscribe(
            'topic={} and data.pipeline.host_id={}'.format(
                constants.PIPELINE_HOST_CONTEXT_CHANGE,
                self.host_connection.id,
            ),
            self._host_context_id_changed,
        )

    def _host_context_id_changed(self, event):
        '''Set the new context ID based on data provided in *event*'''
        # Feed the new context to the client
        self.on_context_changed(event['data']['pipeline']['context_id'])

    def on_context_changed(self, context_id):
        '''Called when the context has been set or changed within the host connection, either from this
        client or remote (other client or the host). Should be overridden by client.'''
        pass

    def unsubscribe_host_context_change(self):
        '''Unsubscribe to client context change events'''
        if self.context_change_subscribe_id:
            self.session.event_hub.unsubscribe(
                self.context_change_subscribe_id
            )
            self.context_change_subscribe_id = None

    # Definition

    def run_definition(self, definition=None, engine_type=None):
        '''
        Calls the :meth:`~ftrack_connect_pipeline.client.HostConnection.run`
        to run the entire given *definition* with the given *engine_type*.

        Callback received at :meth:`_run_callback`
        '''
        # If not definition or engine type passed use the original ones set up
        # in the client
        if not definition:
            definition = self.definition
        if not engine_type:
            engine_type = self.engine_type
        self.host_connection.run(
            definition.to_dict(),
            engine_type,
            callback=self._run_callback,
        )

    def get_schema_from_definition(self, definition):
        '''Return matching schema for the given *definition*'''
        if not self.host_connection:
            self.logger.error("please set the host connection first")
            return
        for schema in self.host_connection.definitions['schema']:
            if (
                schema['properties']['type'].get('default')
                == definition['type']
            ):
                return schema

            self.logger.debug(
                "Schema title: {} and type: {} does not match definition {}".format(
                    schema['title'],
                    schema['properties']['type'].get('default'),
                    definition['name'],
                )
            )

        self.logger.error(
            "Can't find a matching schema for the given definition: {}".format(
                definition.name
            )
        )
        return

    def change_definition(self, definition, schema=None):
        '''
        Assign the given *schema* and the given *definition* as the current
        :obj:`schema` and :obj:`definition`
        '''
        if not self.host_connection:
            self.logger.error("please set the host connection first")
            return
        if not definition:
            self.logger.error("please provide a definition")
            return

        if not schema:
            schema = self.get_schema_from_definition(definition)
        self._schema = schema
        self._definition = definition
        self.change_engine(self.definition['_config']['engine_type'])

    # Plugin

    def run_plugin(self, plugin_data, method, engine_type):
        '''
        Calls the :meth:`~ftrack_connect_pipeline.client.HostConnection.run`
        to run one single plugin.

        Callback received at :meth:`_run_callback`

        *plugin_data* : Dictionary with the plugin information.

        *method* : method of the plugin to be run
        '''
        # Plugin type is constructed using the engine_type and the type of the plugin.
        # (publisher.collector). We have to make sure that plugin_type is in
        # the data argument passed to the host_connection, because we are only
        # passing data to the engine. And the engine_type is only available
        # on the definition.
        plugin_type = '{}.{}'.format(engine_type, plugin_data['type'])
        data = {
            'plugin': plugin_data,
            'plugin_type': plugin_type,
            'method': method,
        }
        self.host_connection.run(
            data, engine_type, callback=self._run_callback
        )

    def _run_callback(self, event):
        '''Callback of the :meth:`~ftrack_connect_pipeline.client.run_plugin'''
        self.logger.debug("_run_callback event: {}".format(event))

    def on_ready(self, callback, time_out=3):
        '''
        calls the given *callback* method when host is been discovered with the
        optional *time_out*
        '''
        self.__callback = callback
        self.discover_hosts(time_out=time_out)

    def change_engine(self, engine_type):
        '''
        Assign the given *engine_type* as the current :obj:`engine_type`
        '''
        self._engine_type = engine_type

    def _on_log_item_added(self, log_item):
        '''Called when a client notify event arrives.'''
        pass

    def on_client_notification(self):
        '''
        Subscribe to topic
        :const:`~ftrack_connect_pipeline.constants.PIPELINE_CLIENT_NOTIFICATION`
        to receive client notifications from the host in :meth:`_notify_client`
        '''
        self.session.event_hub.subscribe(
            'topic={} and data.pipeline.host_id={}'.format(
                constants.PIPELINE_CLIENT_NOTIFICATION, self.host_connection.id
            ),
            self._notify_client,
        )

    def _notify_client(self, event):
        '''
        Callback of the
        :const:`~ftrack_connect_pipeline.constants.PIPELINE_CLIENT_NOTIFICATION`
         event.

        *event*: :class:`ftrack_api.event.base.Event`
        '''
        result = event['data']['pipeline']['result']
        status = event['data']['pipeline']['status']
        plugin_name = event['data']['pipeline']['plugin_name']
        widget_ref = event['data']['pipeline']['widget_ref']
        message = event['data']['pipeline']['message']
        user_data = event['data']['pipeline'].get('user_data') or {}
        user_message = user_data.get('message')
        plugin_id = event['data']['pipeline'].get('plugin_id')

        self._on_log_item_added(LogItem(event['data']['pipeline']))

        if constants.status_bool_mapping[status]:

            self.logger.debug(
                '\n plugin_name: {} \n status: {} \n result: {} \n '
                'message: {} \n user_message: {} \n plugin_id: {}'.format(
                    plugin_name,
                    status,
                    result,
                    message,
                    user_message,
                    plugin_id,
                )
            )

        if (
            status == constants.ERROR_STATUS
            or status == constants.EXCEPTION_STATUS
        ):
            raise Exception(
                'An error occurred during the execution of the '
                'plugin name {} \n message: {}  \n user_message: {} '
                '\n data: {} \n plugin_id: {}'.format(
                    plugin_name, message, user_message, result, plugin_id
                )
            )
