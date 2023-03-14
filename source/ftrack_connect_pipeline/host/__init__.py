# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import uuid
import ftrack_api
import logging
import socket
import os
import time

from ftrack_connect_pipeline.definition import collect, validate
from ftrack_connect_pipeline.host import engine as host_engine
from ftrack_connect_pipeline.host import validation
from ftrack_connect_pipeline import constants, utils

from functools import partial
from ftrack_connect_pipeline.log.log_item import LogItem
from ftrack_connect_pipeline.log import LogDB

logger = logging.getLogger(__name__)


def provide_host_information(
    context_id, host_id, definitions, host_name, event
):
    '''
    Returns dictionary with host id, host name, context id and definition from
    the given *host_id*, *definitions* and *host_name*.

    *host_id* : Host id

    *definitions* : Dictionary with a valid definitions

    *host_name* : Host name
    '''
    logger.debug('providing host_id: {}'.format(host_id))
    host_dict = {
        'host_id': host_id,
        'host_name': host_name,
        'context_id': context_id,
        'definition': definitions,
    }
    return host_dict


class Host(object):

    host_types = [constants.HOST_TYPE]
    '''Compatible Host types for this HOST.'''

    engines = {
        'asset_manager': host_engine.AssetManagerEngine,
        'loader': host_engine.LoaderEngine,
        'opener': host_engine.OpenerEngine,
        'publisher': host_engine.PublisherEngine,
    }
    '''Available engines for this host.'''

    def __repr__(self):
        return '<Host:{0}>'.format(self.host_id)

    @property
    def context_id(self):
        '''Return the the default context id set at host launch'''
        return os.getenv(
            'FTRACK_CONTEXTID',
            os.getenv('FTRACK_TASKID', os.getenv('FTRACK_SHOTID')),
        )

    @context_id.setter
    def context_id(self, value):
        '''Set the context id to *value* and send event to clients (through host connections)'''
        if value == self.context_id:
            return
        os.environ['FTRACK_CONTEXTID'] = value
        self.logger.warning(
            'ftrack host context is now: {}'.format(self.context_id)
        )
        self._ftrack_context_id_changed()

    @property
    def host_id(self):
        '''Returns the current host id.'''
        return self._host_id

    @property
    def host_name(self):
        '''Returns the current host name'''
        if not self.host_id:
            return
        host_types = self.host_id.split("-")[0]
        host_name = '{}-{}'.format(host_types, socket.gethostname())
        return host_name

    @property
    def session(self):
        '''
        Returns instance of :class:`ftrack_api.session.Session`
        '''
        return self._event_manager.session

    def __init__(self, event_manager):
        '''
        Initialise Host with instance of
        :class:`~ftrack_connect_pipeline.event.EventManager`
        '''
        super(Host, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self._host_id = '{}-{}'.format(
            '.'.join(self.host_types), uuid.uuid4().hex
        )
        self._logs = None

        self.logger.debug('initializing {}'.format(self))
        self._event_manager = event_manager
        self.register()

    def run(self, event):
        '''
        Runs the data with the defined engine type of the givent *event*

        Returns result of the engine run.

        *event* : Published from the client host connection at
        :meth:`~ftrack_connect_pipeline.client.HostConnection.run`
        '''

        data = event['data']['pipeline']['data']
        engine_type = event['data']['pipeline']['engine_type']
        asset_type_name = data.get('asset_type')

        Engine = self.engines.get(engine_type)
        if Engine is None:
            raise Exception('No engine of type "{}" found'.format(engine_type))
        engine_runner = Engine(
            self._event_manager, self.host_types, self.host_id, asset_type_name
        )

        if not 'plugin' in data:
            # Run a definition
            try:
                validation.validate_schema(self.__registry['schema'], data)
            except Exception as error:
                self.logger.error(
                    "Can't validate the data {} error: {}".format(data, error)
                )
            runner_result = engine_runner.run_definition(data)
        else:
            runner_result = engine_runner.run(data)

        if runner_result == False:
            self.logger.error("Couldn't publish the data {}".format(data))
        return runner_result

    def on_register_definition(self, event):
        '''
        Callback of the :meth:`register`
        Validates the given *event* and subscribes to the
        :class:`ftrack_api.event.base.Event` events with the topics
        :const:`~ftrack_connnect_pipeline.constants.PIPELINE_DISCOVER_HOST`
        and :const:`~ftrack_connnect_pipeline.constants.PIPELINE_HOST_RUN`

        *event* : Should be a validated and complete definitions, schema and
        packages dictionary coming from
        :func:`ftrack_connect_pipeline_definition.resource.definitions.register.register_definitions`
        '''

        raw_result = event['data']

        if not raw_result:
            return

        # Raw data should contain host_types and definition_paths
        host_types = list(set(raw_result.get("host_types")))
        definition_paths = list(set(raw_result.get("definition_paths")))

        validated_result = self.collect_and_validate_definitions(
            definition_paths, host_types
        )

        self.__registry = validated_result

        handle_event = partial(
            provide_host_information,
            self.context_id,
            self.host_id,
            validated_result,
            self.host_name,
        )

        self._event_manager.subscribe(
            constants.PIPELINE_DISCOVER_HOST, handle_event
        )

        self._event_manager.subscribe(
            '{} and data.pipeline.host_id={}'.format(
                constants.PIPELINE_HOST_RUN, self.host_id
            ),
            self.run,
        )
        self.logger.debug('host {} ready.'.format(self.host_id))

    def collect_and_validate_definitions(self, definition_paths, host_types):
        '''
        Collects all json files from the given *definition_paths* that match
        the given *host_types*
        '''
        start = time.time()

        # collect definitions
        discovered_definitions = collect.collect_definitions(definition_paths)

        # filter definitions
        discovered_definitions = collect.filter_definitions_by_host(
            discovered_definitions, host_types
        )

        # validate schemas
        discovered_definitions = validate.validate_schema(
            discovered_definitions, self.session
        )

        # resolve schemas
        discovered_definitions = collect.resolve_schemas(
            discovered_definitions
        )

        # validate_plugins
        validated_result = self.validate_definition_plugins(
            discovered_definitions
        )

        end = time.time()
        logger.debug('Discover definitions run in: {}s'.format((end - start)))

        for key, value in list(validated_result.items()):
            logger.warning(
                'Valid definitions : {} : {}'.format(key, len(value))
            )

        return validated_result

    def validate_definition_plugins(self, data):
        '''
        Validates the given *data* against the correspondant plugin validator.
        Returns a validated data.

        *data* : Should be a validated and complete definitions and schemas coming from
        :func:`ftrack_connect_pipeline_definition.resource.definitions.register.register_definitions`
        '''
        plugin_validator = validation.PluginDiscoverValidation(
            self.session, self.host_types
        )

        invalid_publishers_idxs = plugin_validator.validate_plugins(
            data['publisher'], constants.PUBLISHER
        )
        if invalid_publishers_idxs:
            for idx in sorted(invalid_publishers_idxs, reverse=True):
                data['publisher'].pop(idx)

        invalid_loaders_idxs = plugin_validator.validate_plugins(
            data['loader'], constants.LOADER
        )
        if invalid_loaders_idxs:
            for idx in sorted(invalid_loaders_idxs, reverse=True):
                data['loader'].pop(idx)

        invalid_openers_idxs = plugin_validator.validate_plugins(
            data['opener'], constants.OPENER
        )
        if invalid_openers_idxs:
            for idx in sorted(invalid_openers_idxs, reverse=True):
                data['opener'].pop(idx)

        return data

    def _init_logs(self):
        '''Delayed initialization of logs, when we know host ID.'''
        if self._logs is None:
            self._logs = LogDB(self._host_id)

    def _on_client_notification(self, event):
        '''
        Callback of the
        :const:`~ftrack_connect_pipeline.constants.PIPELINE_CLIENT_NOTIFICATION`
         event. Stores a log item in host pipeline log DB.

        *event*: :class:`ftrack_api.event.base.Event`
        '''

        self._init_logs()
        self._logs.add_log_item(LogItem(event['data']['pipeline']))

    def register(self):
        '''
        Publishes the :class:`ftrack_api.event.base.Event` with the topic
        :const:`~ftrack_connnect_pipeline.constants.PIPELINE_REGISTER_TOPIC`
        with the first host_type in the list :obj:`host_types` and type definition as the
        data.

        Callback of the event points to :meth:`on_register_definition`
        '''

        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_REGISTER_TOPIC,
            data={
                'pipeline': {
                    'type': 'definition',
                    'host_types': self.host_types,
                }
            },
        )

        self._event_manager.publish(event, self.on_register_definition)

        '''
        Subscribe to topic
        :const:`~ftrack_connect_pipeline.constants.PIPELINE_CLIENT_NOTIFICATION`
        to receive client notifications from the host in :meth:`_notify_client`
        '''
        self.session.event_hub.subscribe(
            'topic={} and data.pipeline.host_id={}'.format(
                constants.PIPELINE_CLIENT_NOTIFICATION, self._host_id
            ),
            self._on_client_notification,
        )

        ''' Listen to context change events for this host and its connected clients'''
        self.session.event_hub.subscribe(
            'topic={} and data.pipeline.host_id={}'.format(
                constants.PIPELINE_CLIENT_CONTEXT_CHANGE, self._host_id
            ),
            self._change_context_id,
        )

    def reset(self):
        '''
        Empty the variables :obj:`host_type`, :obj:`host_id` and :obj:`__registry`
        '''
        self._host_type = []
        self._host_id = None
        self.__registry = {}

    def launch_client(self, name, source=None):
        '''Send a widget launch event, to be picked up by DCC.'''
        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_CLIENT_LAUNCH,
            data={
                'pipeline': {
                    'host_id': self._host_id,
                    'name': name,
                    'source': source,
                }
            },
        )
        self._event_manager.publish(
            event,
        )

    def _change_context_id(self, event):
        if event['data']['pipeline']['host_id'] != self.host_id:
            return
        context_id = event['data']['pipeline']['context_id']
        if context_id != self.context_id:
            self.context_id = context_id

    def _ftrack_context_id_changed(self):
        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_HOST_CONTEXT_CHANGE,
            data={
                'pipeline': {
                    'host_id': self.host_id,
                    'context_id': self.context_id,
                }
            },
        )
        self._event_manager.publish(
            event,
        )
