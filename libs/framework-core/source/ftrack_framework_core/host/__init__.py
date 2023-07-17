# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import uuid
import ftrack_api
import logging
import socket
import os
import time

from ftrack_framework_core.definition import collect, validate
from ftrack_framework_core.host import engine as host_engine
from ftrack_framework_core.host import validation
from ftrack_framework_core import constants, utils

from functools import partial
from ftrack_framework_core.log.log_item import LogItem
from ftrack_framework_core.log import LogDB

logger = logging.getLogger(__name__)

# TODO: this is the discover_host_reply function:
#  1. Double check if this should better be part of the host class as a method.
#  2. Rename it to discover_host_reply_callback or similar?
def provide_host_information(
        host_id, host_name, context_id, definitions, event
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

    # TODO: Engines Dictionary should come from constants.
    #  Should be something CLIENT_NAME:ENGINE:NAME and in here we any have engines = constant.ENGINES_DICT
    engines = {
        constants.PUBLISHER: host_engine.PublisherEngine,
        constants.LOADER: host_engine.LoaderEngine,
        constants.OPENER: host_engine.OpenerEngine,
        constants.ASSET_MANAGER: host_engine.AssetManagerEngine,
        constants.RESOLVER: host_engine.ResolverEngine,
    }
    '''Available engines for this host.'''

    def __repr__(self):
        return '<Host:{0}>'.format(self.host_id)

    @property
    def event_manager(self):
        '''Returns instance of
        :class:`~ftrack_framework_core.event.EventManager`'''
        return self._event_manager

    @property
    def context_id(self):
        '''Return the the default context id set at host launch'''
        #TODO: do we really need to store the context in an env variable?
        # That might be needed for connect but aybe not needed for the framework.
        # In any case, can we remove FTRACK_TASKID and FTRACK_SHOTID?
        return os.getenv(
            'FTRACK_CONTEXTID',
            os.getenv('FTRACK_TASKID', os.getenv('FTRACK_SHOTID')),
        )

    @context_id.setter
    def context_id(self, value):
        '''Set the context id to *value* and send event to clients (through host connections)'''
        if value == self.context_id:
            return
        # TODO: RE-evaluate if we need to store the context to an environment variable
        os.environ['FTRACK_CONTEXTID'] = value
        self.logger.warning(
            'ftrack host context is now: {}'.format(self.context_id)
        )
        self.event_manager.publish.host_context_changed(
            self.host_id,
            self.context_id
        )

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
        :class:`~ftrack_framework_core.event.EventManager`
        '''
        super(Host, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self._host_id = '{}-{}'.format(
            '.'.join(self.host_types), uuid.uuid4().hex
        )
        self._logs = None

        #TODO: initializing host
        self.logger.debug('initializing {}'.format(self))
        self._event_manager = event_manager
        # TODO: split the register method to publish_events, subcribe_events or
        #  find some standard way to do it around all the framework modules. Maybe register its ok, but make sure its
        #  not confusing with the register function of the definitions.
        self.register()

    def run_definition(self, event):
        '''
        Runs the data with the defined engine type of the given *event*

        Returns result of the engine run.

        *event* : Published from the client host connection at
        :meth:`~ftrack_framework_core.client.HostConnection.run`
        '''

        definition = event['data']['definition']
        engine_type = event['data']['engine_type']
        asset_type_name = definition.get('asset_type')

        # TODO: maybe move this to a separated method to get the engine
        Engine = self.engines.get(engine_type)
        if Engine is None:
            # TODO: should we have our own exceptions? So they automatically registers to log as well.
            raise Exception('No engine of type "{}" found'.format(engine_type))
        engine_runner = Engine(
            self._event_manager, self.host_types, self.host_id, asset_type_name
        )

        # TODO: this is a bit magic, at some point we should clarify, run_plugin
        #  or run_definition, but we shouldn't assume that if not plugin in data
        #  we run_definition.
        try:
            validation.validate_schema(self.__registry['schema'], definition)
        except Exception as error:
            self.logger.error(
                "Can't validate definition {} error: {}".format(definition, error)
            )
        runner_result = engine_runner.run_definition(definition)

        if runner_result == False:
            # TODO: fix this log. We don't know if we are publishing loading or what.
            self.logger.error("Couldn't run efinition {}".format(definition))
        return runner_result

    def run_plugin(self, event):
        '''
        Runs the data with the defined engine type of the givent *event*

        Returns result of the engine run.

        *event* : Published from the client host connection at
        :meth:`~ftrack_framework_core.client.HostConnection.run`
        '''

        plugin = event['data']['plugin']
        plugin_type = event['data']['plugin_type']
        method = event['data']['method']
        engine_type = event['data']['engine_type']

        Engine = self.engines.get(engine_type)
        if Engine is None:
            # TODO: should we have our own exceptions? So they automatically registers to log as well.
            raise Exception('No engine of type "{}" found'.format(engine_type))
        engine_runner = Engine(
            self._event_manager, self.host_types, self.host_id, None
        )

        runner_result = engine_runner.run_plugin(plugin, plugin_type, method)

        if runner_result == False:
            # TODO: fix this log. We don't know if we are publishing loading or what.
            self.logger.error("Couldn't run plugin {}".format(plugin))
        return runner_result

    #TODO: rename to on_register_definition_callback? (Same for all the callbacks in all the modules)
    def on_register_definition(self, event):
        '''
        Callback of the :meth:`register`
        Validates the given *event* and subscribes to the
        :class:`ftrack_api.event.base.Event` events with the topics
        :const:`~ftrack_connnect_pipeline.constants.DISCOVER_HOST_TOPIC`
        and :const:`~ftrack_connnect_pipeline.constants.HOST_RUN_DEFINITION_TOPIC`

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

        # TODO: rename this to __schema_registry or __definitions_registry. Also make sure its initialized in the init.
        self.__registry = validated_result

        discover_host_callback_reply = partial(
            provide_host_information,
            self.host_id,
            self.host_name,
            self.context_id,
            validated_result,
        )

        self.event_manager.subscribe.discover_host(
            callback=discover_host_callback_reply
        )

        # TODO: change the run callback to run_definiton
        self.event_manager.events.subscribe.host_run_definition(self.host_id, self.run_definition)
        # TODO: create the run_plugin method (pick the desired parts from the current self.run plugin)
        #  Carefully, run plugin topic was already used by engines to be able to run plugins, so the run plugin function wasn't existing int the host. We will have to separate this 2 events maybe.
        self.event_manager.events.subscribe.host_run_plugin(self.host_id, self.run_plugin)
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
            self.event_manager, self.host_types
        )
        #TODO: all client names should be cosntants. Also try to make this smaller,
        # and automatically extensible by a list from cosntants.
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
        :const:`~ftrack_framework_core.constants.NOTIFY_CLIENT_TOPIC`
         event. Stores a log item in host pipeline log DB.

        *event*: :class:`ftrack_api.event.base.Event`
        '''

        self._init_logs()
        # TODO: all data/pipeline events should come from data/framework or data/  events.
        self._logs.add_log_item(LogItem(event['data']['pipeline']))

    def register(self):
        '''
        Publishes the :class:`ftrack_api.event.base.Event` with the topic
        :const:`~ftrack_connnect_pipeline.constants.DISCOVER_DEFINITION_TOPIC`
        with the first host_type in the list :obj:`host_types` and type definition as the
        data.

        Callback of the event points to :meth:`on_register_definition`
        '''

        self.event_manager.publish.discover_definition(host_types=self.host_types)

        '''
        Subscribe to topic
        :const:`~ftrack_framework_core.constants.NOTIFY_CLIENT_TOPIC`
        to receive client notifications from the host in :meth:`_notify_client_callback`
        '''
        self.event_manager.subscribe.notify_client(
            self.host_id, self._on_client_notification
        )

        ''' Listen to context change events for this host and its connected clients'''
        self.event_manager.subscribe.client_context_changed(
            self.host_id, self._change_context_id
        )

    def reset(self):
        '''
        Empty the variables :obj:`host_type`, :obj:`host_id` and :obj:`__registry`
        '''
        self._host_type = []
        self._host_id = None
        #TODO: rename this to __schema_registry ot __definitions_registry also make sure is initialized in the init.
        self.__registry = {}

    # TODO: rename this to client_context_change_callback
    def _change_context_id(self, event):
        if event['data']['pipeline']['host_id'] != self.host_id:
            return
        context_id = event['data']['pipeline']['context_id']
        if context_id != self.context_id:
            self.context_id = context_id
