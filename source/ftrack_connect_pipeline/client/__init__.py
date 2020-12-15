# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import time
import logging
import copy
import ftrack_api
from ftrack_connect_pipeline import utils
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.log.log_item import LogItem


class HostConnection(object):
    '''
    Host Connection Base class.
    This class is used to communicate from the client to the host.
    '''

    @property
    def context(self):
        '''Returns the current context id'''
        return self._context

    @context.setter
    def context(self, value):
        '''Sets the current context id with the given *value*'''
        self._context = value

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
    def definitions(self):
        '''Returns the current definitions.'''
        return self._raw_host_data['definition']

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

        *host_data* : Diccionary containing the host information.
        :py:func:`~ftrack_connect_pipeline.host.provide_host_information`

        '''
        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )

        copy_data = copy.deepcopy(host_data)

        self._logs = []
        self._event_manager = event_manager
        self._raw_host_data = copy_data

        self.context = self._raw_host_data['context_id']

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
                    'engine_type': engine
                }
            }
        )
        self._event_manager.publish(
            event, callback
        )


class Client(object):
    '''
    Base client class.
    '''

    ui_types = [constants.UI_TYPE]
    '''Compatible UI for this client.'''
    definition_filter = None
    '''Use only definitions that matches the definition_filter'''

    def __repr__(self):
        return '<Client:{0}>'.format(self.ui_types)

    def __del__(self):
        self.logger.debug('Closing {}'.format(self))

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
    def context(self):
        '''Returns the context id.'''
        return self._context_id

    @context.setter
    def context(self, context_id):
        ''' Sets the context id. '''
        if not isinstance(context_id, basestring):
            raise ValueError('Context should be in form of a string.')

        self._context_id = context_id

    @property
    def host_connection(self):
        '''
        Return instance of
        :class:`~ftrack_connect_pipeline.client.HostConnection`
        '''
        return self._host_connection

    @property
    def schema(self):
        '''Return the current schema.'''
        return self._schema

    @property
    def definition(self):
        '''Returns the current definition.'''
        return self._definition

    @property
    def engine_type(self):
        '''Return the current engine type'''
        return self._engine_type

    @property
    def host_connections(self):
        '''Return the current list of host_connections'''
        return self._host_connections

    @property
    def logs(self):
        '''Returns all the saved logs'''
        return self._logs

    def __init__(self, event_manager):
        '''
        Initialise Client with instance of
        :class:`~ftrack_connect_pipeline.event.EventManager`
        '''
        self._packages = {}
        self._current = {}

        self._context_id = utils.get_current_context()
        self._host_connections = []
        self._connected = False
        self._host_connection = None
        self._logs = []
        self._schema = None
        self._definition = None
        self.current_package = None

        self.__callback = None
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self._event_manager = event_manager
        self.logger.info('Initialising {}'.format(self))

    def discover_hosts(self, time_out=3):
        '''
        Find for available hosts during the optional *time_out* and Returns
        a list of discovered :class:`~ftrack_connect_pipeline.client.HostConnection`.
        '''
        # discovery host loop and timeout.
        start_time = time.time()
        self.logger.info('time out set to {}:'.format(time_out))
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

        return self.host_connections

    def _host_discovered(self, event):
        '''
        Callback, add the :class:`~ftrack_connect_pipeline.client.HostConnection`
        of the new discovered :class:`~ftrack_connect_pipeline.host.HOST` from
        the given *event*.

        *event*: :class:`ftrack_api.event.base.Event`
        '''
        if not event['data']:
            return
        host_connection = HostConnection(self._event_manager, event['data'])
        if host_connection not in self.host_connections:
            self._host_connections.append(host_connection)

        self._connected = True

    def _discover_hosts(self):
        '''
        Publish an event with the topic
        :py:data:`~ftrack_connect_pipeline.constants.PIPELINE_DISCOVER_HOST`
        with the callback
        py:meth:`~ftrack_connect_pipeline.client._host_discovered`
        '''
        self._host_connections = []
        discover_event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_DISCOVER_HOST
        )

        self._event_manager.publish(
            discover_event,
            callback=self._host_discovered
        )

    def run_definition(self, definition, engine_type):
        '''
        Calls the :meth:`~ftrack_connect_pipeline.client.HostConnection.run`
        to run the entire given *definition* with the given *engine_type*.

        Callback received at :meth:`_run_callback`
        '''
        self.host_connection.run(
            definition, engine_type, self._run_callback
        )

    def run_plugin(self, plugin_data, method, engine_type):
        '''
        Calls the :meth:`~ftrack_connect_pipeline.client.HostConnection.run`
        to run one single plugin.

        Callback received at :meth:`_run_callback`

        *plugin_data* : Dictionary with the plugin information.

        *method* : method of the plugin to be run
        '''
        # Plugin type is constructed using the engine_type and the plugin_type
        # (publisher.collector). We have to make sure that plugin_type is in
        # the data argument passed to the host_connection, because we are only
        # passing data to the engine. And the engine_type is only available
        # on the definition.
        plugin_type = '{}.{}'.format(engine_type, plugin_data['plugin_type'])
        data = {
            'plugin': plugin_data,
            'plugin_type': plugin_type,
            'method': method
        }
        self.host_connection.run(
            data, engine_type, self._run_callback
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

    def change_host(self, host_connection):
        '''
        Assign the given *host_connection* as the current :obj:`host_connection`

        *host_connection* : should be instance of
        :class:`~ftrack_connect_pipeline.client.HostConnection`
        '''
        if not host_connection:
            return

        self.logger.info('connection: {}'.format(host_connection))
        self._host_connection = host_connection
        # set current context to host
        self.change_context(self.host_connection.context or self.context)
        self.on_client_notification()

    def change_definition(self, schema, definition):
        '''
        Assign the given *schema* and the given *definition* as the current
        :obj:`schema` and :obj:`definition`
        '''
        if not self.host_connection:
            self.logger.error("please set the host connection first")
            return

        self.logger.debug('schema: {}'.format(schema))
        self.logger.debug('definition: {}'.format(definition))

        self._schema = schema
        self._definition = definition

        self.current_package = self.get_current_package()

        self.change_engine(self.definition['_config']['engine_type'])

    def change_engine(self, engine_type):
        '''
        Assign the given *engine_type* as the current :obj:`engine_type`
        '''
        self._engine_type = engine_type

    def get_current_package(self):
        '''
        Returns the package of the current :obj:`definition`
        '''
        if not self.host_connection or not self.definition:
            self.logger.error(
                "please set the host connection and the definition first"
            )
            return

        for package in self.host_connection.definitions['package']:
            if package['name'] == self.definition.get('package'):
                return package
        return None

    def change_context(self, context_id):
        '''
        Assign the given *context_id* as the current :obj:`context` and to the
        :attr:`~ftrack_connect_pipeline.client.HostConnection.context`
        '''
        self.context = context_id
        self._host_connection.context = context_id

    def _add_log_item(self, log_item):
        '''
        Append the given *log_item* to the current :obj:`logs` list
        '''
        self._logs.append(log_item)

    def on_client_notification(self):
        '''
        Subscribe to topic
        :const:`~ftrack_connect_pipeline.constants.PIPELINE_CLIENT_NOTIFICATION`
        to receive client notifications from the host in :meth:`_notify_client`
        '''
        self.session.event_hub.subscribe(
            'topic={} and data.pipeline.host_id={}'.format(
                constants.PIPELINE_CLIENT_NOTIFICATION,
                self.host_connection.id
            ),
            self._notify_client
        )

    def _notify_client(self, event):
        '''
        Callback of the
        :const:`~ftrack_connect_pipeline.constants.PIPELINE_CLIENT_NOTIFICATION`
         event.

        *event*: :class:`ftrack_api.event.base.Event`
        '''
        '''callback to notify the client with the *event* data'''
        result = event['data']['pipeline']['result']
        status = event['data']['pipeline']['status']
        plugin_name = event['data']['pipeline']['plugin_name']
        widget_ref = event['data']['pipeline']['widget_ref']
        message = event['data']['pipeline']['message']

        self._add_log_item(LogItem(event['data']['pipeline']))

        if constants.status_bool_mapping[status]:

            self.logger.debug(
                'plugin_name: {} \n status: {} \n result: {} \n '
                'message: {}'.format(
                    plugin_name, status, result, message
                )
            )

        if (
                status == constants.ERROR_STATUS or
                status == constants.EXCEPTION_STATUS
        ):
            raise Exception(
                'An error occurred during the execution of the '
                'plugin name {} \n message: {} \n data: {}'.format(
                    plugin_name, message, result
                )
            )
