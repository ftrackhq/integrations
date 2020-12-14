# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import time
import logging
import copy
import ftrack_api

import sqlite3
import tempfile
import os
import json

from ftrack_connect_pipeline import utils
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.log.log_item import LogItem


class LogDB(object):
    table_name = 'LOGMGR'
    db_name = 'pipeline_asset_manager.db'

    def __del__(self):
        self.connection.close()

    @property
    def connection(self):
        return self._connection

    def __init__(self, name='default'):
        super(LogDB, self).__init__()
        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )

        temp_folder = tempfile.gettempdir()
        db_name = '{}_{}'.format(name, self.db_name)
        destination_db = os.path.join(temp_folder, db_name)

        self.logger.debug('Creating db file {}'.format(destination_db))
        self._connection = sqlite3.connect(destination_db)
        self.create_tables()
    
    def create_tables(self):
        self.connection.execute(
            '''CREATE TABLE IF NOT EXISTS {0} (id INTEGER PRIMARY KEY, data JSON NOT NULL);'''.format(
                self.table_name
            )
        )

    def add_log_item(self, log_data):

        self.connection.execute(
            '''INSERT INTO {0}(data) VALUES (?)'''.format(self.table_name),
            [json.dumps(log_data)]
        )
        self.connection.commit()

    def get_log_items(self):
        result = []
        return_values =  self.connection.execute(
            'select data from {0}'.format(self.table_name)
        ).fetchall()

        for return_value in return_values:
            raw_log = json.loads(return_value[0])
            log_item = LogItem(raw_log)
            result.append(log_item)

        return result


class HostConnection(object):

    @property
    def context(self):
        return self._context

    @context.setter
    def context(self, value):
        '''Sets the engine_type with the given *value*'''
        self._context = value

    @property
    def session(self):
        '''Return session'''
        return self._event_manager.session

    @property
    def definitions(self):
        return self._raw_host_data['definition']

    @property
    def id(self):
        return self._raw_host_data['host_id']

    @property
    def name(self):
        return self._raw_host_data['host_name']

    @property
    def host_types(self):
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
        '''Initialise with *event_manager* , and *host_data*

        *event_manager* should be the
        :class:`ftrack_connect_pipeline.event.EventManager`instance to
        communicate to the event server.

        *host_data* Diccionary containing the host information.
        '''
        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )

        copy_data = copy.deepcopy(host_data)

        self._event_manager = event_manager
        self._raw_host_data = copy_data

        self.context = self._raw_host_data['context_id']

    def run(self, data, engine, callback=None):
        '''Send *data* to the host through the PIPELINE_HOST_RUN topic.'''
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
    definition_filter = None

    def __repr__(self):
        return '<Client:{0}>'.format(self.ui_types)

    def __del__(self):
        self.logger.debug('Closing {}'.format(self))

    @property
    def session(self):
        '''Return session'''
        return self._event_manager.session

    @property
    def connected(self):
        '''Return bool of client connected to a host'''
        return self._connected

    @property
    def context(self):
        return self._context_id

    @context.setter
    def context(self, context_id):
        if not isinstance(context_id, basestring):
            raise ValueError('Context should be in form of a string.')

        self._context_id = context_id

    @property
    def host_connection(self):
        '''Return the current _host_connection'''
        return self._host_connection

    @property
    def schema(self):
        '''Return the current _host_connection'''
        return self._schema

    @property
    def definition(self):
        '''Return the current _host_connection'''
        return self._definition

    @property
    def engine_type(self):
        '''Return the current _host_connection'''
        return self._engine_type

    @property
    def host_connections(self):
        '''Return the current list of host_connections'''
        return self._host_connections

    @property
    def logs(self):
        return self._logs.get_log_items()

    def _add_log_item(self, log_item):
        self.logger.info('Adding log item ::{} {}'.format(type(log_item), log_item))
        self._logs.add_log_item(log_item)

    def __init__(self, event_manager):
        '''Initialise with *event_manager* , and optional *ui* List

        *event_manager* should be the
        :class:`ftrack_connect_pipeline.event.EventManager`instance to
        communicate to the event server.

        *ui* List of valid ui compatibilities.
        '''
        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )
        self._packages = {}
        self._current = {}

        self._context_id = utils.get_current_context()
        self._host_connections = []
        self._connected = False
        self._host_connection = None
        self._logs = LogDB()

        self._schema = None
        self._definition = None
        self.current_package = None

        self.__callback = None

        self._event_manager = event_manager
        self.logger.info('Initialising {}'.format(self))

    def discover_hosts(self, time_out=3):
        '''Returns a list of discovered host_connections during the optional *time_out*'''
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
        '''callback, adds new host_connections connection from the given *event*'''
        if not event['data']:
            return
        host_connection = HostConnection(self._event_manager, event['data'])
        if host_connection not in self.host_connections:
            self._host_connections.append(host_connection)

        self._connected = True

    def _discover_hosts(self):
        '''Event to discover new available host_connections.'''
        self._host_connections = []
        discover_event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_DISCOVER_HOST
        )

        self._event_manager.publish(
            discover_event,
            callback=self._host_discovered
        )

    def run_definition(self, definition, engine_type):
        '''Runs the complete given *definition* with the given engine_type.'''
        self.host_connection.run(
            definition, engine_type, self._run_callback
        )

    def run_plugin(self, plugin_data, method, engine_type):
        '''Function called to run one single plugin *plugin_data* with the
        plugin information and the *method* to be run has to be passed'''
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
        self.logger.debug("_run_callback event: {}".format(event))

    def on_ready(self, callback, time_out=3):
        '''calls the given *callback* when host is been discovered with the
        optional *time_out*

        *callback* Function to call when a host has been discovered

        *time_out* Optional time out time to look for a host

        '''
        self.__callback = callback
        self.discover_hosts(time_out=time_out)

    def change_host(self, host_connection):
        ''' Triggered when host_changed is called from the host_selector.'''
        if not host_connection:
            return

        self.logger.info('connection: {}'.format(host_connection))
        self._host_connection = host_connection
        # set current context to host
        self.change_context(self.host_connection.context or self.context)
        self.on_client_notification()

    def change_definition(self, schema, definition):
        ''' Triggered when definition_changed is called from the host_selector.
        Generates the widgets interface from the given *host_connection*,
        *schema* and *definition*'''
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
        self._engine_type = engine_type

    def get_current_package(self):
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
        self.context = context_id
        self._host_connection.context = context_id


    def on_client_notification(self):
        '''Subscribe to PIPELINE_CLIENT_NOTIFICATION topic to receive client
        notifications from the host'''
        self.session.event_hub.subscribe(
            'topic={} and data.pipeline.host_id={}'.format(
                constants.PIPELINE_CLIENT_NOTIFICATION,
                self.host_connection.id
            ),
            self._notify_client
        )

    def _notify_client(self, event):
        '''callback to notify the client with the *event* data'''
        result = event['data']['pipeline']['result']
        status = event['data']['pipeline']['status']
        plugin_name = event['data']['pipeline']['plugin_name']
        message = event['data']['pipeline']['message']

        self._add_log_item(event['data']['pipeline'])

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
